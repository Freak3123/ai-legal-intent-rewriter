"""FastAPI entry point — orchestrates the full pipeline.

This module is intentionally thin: it only does HTTP, auth, and timing.
All real work happens in `app.pipeline.*`. Each pipeline module is
independently testable and replaceable.
"""

from __future__ import annotations

import json
import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app import __version__
from app.config import model_versions, settings
from app.pipeline import classify, ingest, ner, rewrite, risk, segment
from app.pipeline.ingest import IngestionResult
from app.schemas import (
    AnalyzeOptions,
    AnalyzeRequest,
    AnalyzeResponse,
    CharSpan,
    Clause,
    HealthResponse,
    Metrics,
    ModelVersionsInfo,
    TimingMs,
)

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("legal-rewriter-ml")

# State shared across requests
_state: dict[str, Any] = {"started_at": time.time()}

# -----------------------------------------------------------------------------
# Lifespan: load models once at startup
# -----------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Startup/shutdown hook. Pre-loads HF + spaCy models so the first request is cheap."""
    logger.info("Starting up — version %s", __version__)
    try:
        classify.warm_up()
        rewrite.warm_up()
        ner.warm_up()
    except Exception as exc:  # never block startup on a model load failure
        logger.warning("model warm-up encountered an error: %s", exc)
    _state["models_loaded"] = {
        "classifier": classify._hf_state not in (None, (None, None))  # type: ignore[attr-defined]
        or classify._load_sklearn_model() is not None,  # type: ignore[attr-defined]
        "rewriter": rewrite._hf_state not in (None, (None, None)),  # type: ignore[attr-defined]
        "ner": True,
    }
    logger.info("Startup complete (models_loaded=%s)", _state["models_loaded"])
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="AI Legal Intent Rewriter — ML Service",
    version=__version__,
    description="ML inference service for the AI Legal Intent Rewriter project. "
    "See docs/api-contract.md in the main repo for the JSON contract.",
    lifespan=lifespan,
)

# -----------------------------------------------------------------------------
# CORS
# -----------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,  # No cookies — auth is via Bearer token
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600,
)

# -----------------------------------------------------------------------------
# Auth dependency — optional Bearer token
# -----------------------------------------------------------------------------

_bearer = HTTPBearer(auto_error=False)


async def verify_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> None:
    """If ML_SERVICE_TOKEN is set, require it as a Bearer token. Otherwise no-op."""
    if not settings.ml_service_token:
        return  # auth disabled
    if credentials is None or credentials.credentials != settings.ml_service_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing bearer token",
        )


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------


@app.get("/")
async def root() -> dict[str, str]:
    """Friendly root for HF Spaces visitors who land at the base URL."""
    return {
        "service": "AI Legal Intent Rewriter — ML",
        "version": __version__,
        "docs": "/docs",
        "health": "/v1/health",
    }


@app.get("/v1/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Readiness check. Use this to pre-warm a sleeping HF Space."""
    return HealthResponse(
        status="ready",
        models_loaded=_state.get("models_loaded", {}),
        uptime_seconds=int(time.time() - _state["started_at"]),
        version=__version__,
    )


@app.post(
    "/v1/analyze",
    response_model=AnalyzeResponse,
    dependencies=[Depends(verify_token)],
)
async def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    """Run the full pipeline on input text.

    Pipeline order: ingest → segment → classify → ner → rewrite → risk
    """
    if len(req.text) > settings.max_text_length:
        raise HTTPException(
            status_code=413,
            detail={"code": "FILE_TOO_LARGE", "message": "Text exceeds maximum length"},
        )

    t0 = time.perf_counter()
    ingestion = ingest.ingest_text(req.text)
    ingest_ms = _ms_since(t0)
    return _run_pipeline(ingestion, req.options, ingest_ms=ingest_ms)


@app.post(
    "/v1/analyze/pdf",
    response_model=AnalyzeResponse,
    dependencies=[Depends(verify_token)],
)
async def analyze_pdf(
    file: UploadFile = File(...),
    options: str | None = Form(None),
) -> AnalyzeResponse:
    """Run the full pipeline on a PDF upload (digital or scanned).

    The ``options`` form field, if present, is a JSON-encoded ``AnalyzeOptions``
    object — same shape as ``options`` on the text-mode endpoint.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_INPUT", "message": "Expected a .pdf file upload"},
        )

    raw = await file.read()
    if len(raw) > settings.max_pdf_size_bytes:
        raise HTTPException(
            status_code=413,
            detail={"code": "FILE_TOO_LARGE", "message": "PDF exceeds maximum size"},
        )

    parsed_options = AnalyzeOptions()
    if options:
        try:
            parsed_options = AnalyzeOptions(**json.loads(options))
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=400,
                detail={"code": "INVALID_INPUT", "message": f"Bad options JSON: {exc}"},
            ) from exc

    t0 = time.perf_counter()
    try:
        ingestion = ingest.ingest_pdf_bytes(raw)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail={"code": "OCR_FAILED", "message": str(exc)},
        ) from exc
    ingest_ms = _ms_since(t0)

    return _run_pipeline(ingestion, parsed_options, ingest_ms=ingest_ms)


def _run_pipeline(
    ingestion: IngestionResult,
    options: AnalyzeOptions,
    *,
    ingest_ms: int,
) -> AnalyzeResponse:
    """Shared pipeline runner used by both /v1/analyze and /v1/analyze/pdf."""
    timings: dict[str, int] = {"ingestion": ingest_ms}

    t0 = time.perf_counter()
    segments = segment.segment_clauses(ingestion.text, max_clauses=options.max_clauses)
    timings["segmentation"] = _ms_since(t0)

    classify_total = ner_total = rewrite_total = risk_total = 0.0
    clauses: list[Clause] = []
    confidences: list[float] = []
    high_risk = medium_risk = 0

    for ordinal, seg in enumerate(segments):
        clause_text = seg.text[: settings.max_clause_length]

        t0 = time.perf_counter()
        classification = classify.classify_clause(clause_text, include_top_k=options.include_top_k)
        classify_total += _seconds_since(t0)

        t0 = time.perf_counter()
        entities = ner.extract_entities(clause_text)
        ner_total += _seconds_since(t0)

        t0 = time.perf_counter()
        clause_rewrite = rewrite.rewrite_clause(clause_text, classification.label)
        rewrite_total += _seconds_since(t0)

        t0 = time.perf_counter()
        clause_risk = risk.assess_risk(clause_text, classification.label)
        risk_total += _seconds_since(t0)

        clauses.append(
            Clause(
                ordinal=ordinal,
                original_text=clause_text,
                char_span=CharSpan(start=seg.start, end=seg.end),
                classification=classification,
                entities=entities,
                rewrite=clause_rewrite,
                risk=clause_risk,
            )
        )
        confidences.append(classification.confidence)
        if clause_risk.level == "high":
            high_risk += 1
        elif clause_risk.level == "medium":
            medium_risk += 1

    timings["classification"] = int(classify_total * 1000)
    timings["ner"] = int(ner_total * 1000)
    timings["rewriting"] = int(rewrite_total * 1000)
    timings["risk_flagging"] = int(risk_total * 1000)
    timings["total"] = sum(timings.values())

    return AnalyzeResponse(
        ingestion_method=ingestion.method,
        page_count=ingestion.page_count,
        clauses=clauses,
        metrics=Metrics(
            total_clauses=len(clauses),
            high_risk_count=high_risk,
            medium_risk_count=medium_risk,
            avg_confidence=round(
                sum(confidences) / len(confidences) if confidences else 0.0, 3
            ),
        ),
        model_versions=ModelVersionsInfo(
            classifier=model_versions.classifier,
            rewriter=model_versions.rewriter,
            ner_version=model_versions.ner_version,
        ),
        timing_ms=TimingMs(**timings),
    )


# -----------------------------------------------------------------------------
# Error handler — translate uncaught exceptions to the contract error shape
# -----------------------------------------------------------------------------


@app.exception_handler(Exception)
async def unhandled_exception(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Something went wrong inside the ML service",
                "details": {"type": type(exc).__name__},
            }
        },
    )


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def _ms_since(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


def _seconds_since(start: float) -> float:
    return time.perf_counter() - start
