"""Response schemas. Mirrors docs/api-contract.md exactly.

When you change anything here, update:
  1. docs/api-contract.md
  2. apps/web/types/index.ts
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------

ClassificationLabel = Literal[
    "LIABILITY",
    "TERMINATION",
    "PAYMENT",
    "CONFIDENTIALITY",
    "INDEMNIFICATION",
    "INTELLECTUAL_PROPERTY",
    "GOVERNING_LAW",
    "DISPUTE_RESOLUTION",
    "DEFINITIONS",
    "RENEWAL",
    "WARRANTY",
    "OTHER",
]

EntityType = Literal["DATE", "AMOUNT", "PARTY", "RIGHT", "OBLIGATION", "CONDITION"]

RiskLevel = Literal["low", "medium", "high"]

IngestionMethod = Literal["pdfjs", "pymupdf", "tesseract-ocr", "text-direct"]

RewriteMethod = Literal["model", "template-fallback"]

# -----------------------------------------------------------------------------
# Building blocks
# -----------------------------------------------------------------------------


class CharSpan(BaseModel):
    start: int
    end: int


class TopK(BaseModel):
    label: ClassificationLabel
    score: float


class Classification(BaseModel):
    label: ClassificationLabel
    confidence: float = Field(..., ge=0.0, le=1.0)
    top_k: list[TopK]


class Entity(BaseModel):
    text: str
    type: EntityType
    start: int
    end: int


class Rewrite(BaseModel):
    text: str
    readability_score: float
    method: RewriteMethod


class Risk(BaseModel):
    level: RiskLevel
    score: float = Field(..., ge=0.0, le=1.0)
    triggers: list[str]


class Clause(BaseModel):
    ordinal: int
    original_text: str
    char_span: CharSpan
    classification: Classification
    entities: list[Entity]
    rewrite: Rewrite
    risk: Risk


# -----------------------------------------------------------------------------
# Top-level responses
# -----------------------------------------------------------------------------


class Metrics(BaseModel):
    total_clauses: int
    high_risk_count: int
    medium_risk_count: int
    avg_confidence: float


class ModelVersionsInfo(BaseModel):
    classifier: str
    rewriter: str
    ner_version: str


class TimingMs(BaseModel):
    ingestion: int
    segmentation: int
    classification: int
    ner: int
    rewriting: int
    risk_flagging: int
    total: int


class AnalyzeResponse(BaseModel):
    ingestion_method: IngestionMethod
    page_count: int
    clauses: list[Clause]
    metrics: Metrics
    model_versions: ModelVersionsInfo
    timing_ms: TimingMs


class HealthResponse(BaseModel):
    status: Literal["ready", "loading", "error"]
    models_loaded: dict[str, bool]
    uptime_seconds: int
    version: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorBody
