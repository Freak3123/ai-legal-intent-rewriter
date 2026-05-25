"""Clause classification.

Three-layer resolver:

1. HF transformer (`AutoModelForSequenceClassification`) when the pin in
   ``app.config.model_versions.classifier`` looks like a Hub repo ID (contains
   "/"). This is the production path once the fine-tuned Legal-BERT is pushed.
2. Local sklearn pickle (``app/models/clause_classifier.pkl``). The TF-IDF +
   LogReg baseline. Used when the HF pin doesn't resolve or no GPU is wanted.
3. Keyword heuristic. Last-resort fallback so the service always responds.

The first call triggers loading; results are cached in module-level globals so
subsequent calls are cheap. ``app.main`` calls ``warm_up()`` at startup to take
the load cost out of the first request.
"""

from __future__ import annotations

import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, get_args

from app.config import model_versions
from app.schemas import Classification, ClassificationLabel, TopK

logger = logging.getLogger(__name__)

_ARTIFACT_PATH = Path(__file__).resolve().parents[1] / "models" / "clause_classifier.pkl"

_VALID_LABELS: frozenset[str] = frozenset(get_args(ClassificationLabel))
_MAX_INPUT_LENGTH = 256

# Module-level cache for the loaded HF model + tokenizer. None means "not
# attempted yet"; (None, None) means "tried and failed".
_hf_state: tuple[Any, Any] | None = None


def _is_hf_pin(pin: str) -> bool:
    return "/" in pin and not pin.startswith(".")


def _load_hf_model() -> tuple[Any, Any] | tuple[None, None]:
    """Load the fine-tuned Legal-BERT from the HF Hub. Caches the result."""
    import os

    global _hf_state
    if _hf_state is not None:
        return _hf_state

    if os.environ.get("LEGAL_REWRITER_DISABLE_HF") == "1":
        _hf_state = (None, None)
        return _hf_state

    pin = model_versions.classifier
    if not _is_hf_pin(pin):
        _hf_state = (None, None)
        return _hf_state

    try:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        logger.info("loading HF classifier %s", pin)
        tokenizer = AutoTokenizer.from_pretrained(pin)
        model = AutoModelForSequenceClassification.from_pretrained(pin)
        model.eval()
        if torch.cuda.is_available():
            model = model.to("cuda")
        _hf_state = (model, tokenizer)
        logger.info("HF classifier loaded (labels=%d)", model.config.num_labels)
    except Exception as exc:
        logger.warning("failed to load HF classifier %s: %s", pin, exc)
        _hf_state = (None, None)
    return _hf_state


@lru_cache(maxsize=1)
def _load_sklearn_model() -> Any | None:
    """Load the TF-IDF + LogReg pickle. Cached."""
    if not _ARTIFACT_PATH.exists():
        return None
    try:
        import joblib

        return joblib.load(_ARTIFACT_PATH)
    except Exception as exc:
        logger.warning("failed to load sklearn classifier: %s", exc)
        return None


def warm_up() -> None:
    """Trigger model loads at app startup so the first request is cheap."""
    _load_hf_model()
    _load_sklearn_model()


def classify_clause(text: str, include_top_k: int = 3) -> Classification:
    """Classify one clause through the best available backend."""
    hf_model, hf_tokenizer = _load_hf_model()
    if hf_model is not None:
        return _classify_with_hf(hf_model, hf_tokenizer, text, include_top_k)

    sklearn_model = _load_sklearn_model()
    if sklearn_model is not None:
        return _classify_with_sklearn(sklearn_model, text, include_top_k)

    return _classify_with_keywords(text, include_top_k)


def _classify_with_hf(
    model: Any, tokenizer: Any, text: str, include_top_k: int
) -> Classification:
    import torch

    device = next(model.parameters()).device
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=_MAX_INPUT_LENGTH,
        padding=False,
    ).to(device)
    with torch.no_grad():
        logits = model(**inputs).logits[0]
    probs = torch.softmax(logits, dim=-1).cpu().tolist()

    id2label: dict[int, str] = model.config.id2label
    pairs = sorted(
        ((id2label[i], probs[i]) for i in range(len(probs))),
        key=lambda p: p[1],
        reverse=True,
    )
    top_label, top_score = pairs[0]
    if top_label not in _VALID_LABELS:
        top_label = "OTHER"

    top_k_list: list[TopK] = []
    for label, score in pairs[: max(1, include_top_k)]:
        if label not in _VALID_LABELS:
            continue
        top_k_list.append(TopK(label=label, score=round(float(score), 3)))

    return Classification(
        label=top_label,
        confidence=round(float(top_score), 3),
        top_k=top_k_list,
    )


def _classify_with_sklearn(
    model: Any, text: str, include_top_k: int
) -> Classification:
    proba = model.predict_proba([text])[0]
    classes: list[str] = list(model.classes_)
    pairs = sorted(zip(classes, proba, strict=True), key=lambda p: p[1], reverse=True)

    top_label, top_score = pairs[0]
    if top_label not in _VALID_LABELS:
        top_label = "OTHER"

    top_k_list: list[TopK] = []
    for label, score in pairs[: max(1, include_top_k)]:
        if label not in _VALID_LABELS:
            continue
        top_k_list.append(TopK(label=label, score=round(float(score), 3)))

    return Classification(
        label=top_label,
        confidence=round(float(top_score), 3),
        top_k=top_k_list,
    )


# -----------------------------------------------------------------------------
# Keyword fallback (used when neither HF nor sklearn artefacts load)
# -----------------------------------------------------------------------------

_KEYWORDS: dict[ClassificationLabel, list[str]] = {
    "TERMINATION": [
        "terminate", "termination", "expiry", "expire", "renewal", "auto-renew",
        "automatic renewal", "end this agreement", "notice of termination",
    ],
    "RENEWAL": ["renewal", "renew", "automatically renew", "successive terms"],
    "LIABILITY": [
        "liable", "liability", "in no event shall", "consequential damages",
        "indirect damages", "punitive damages", "loss of profits", "uncapped",
    ],
    "INDEMNIFICATION": [
        "indemnify", "indemnification", "hold harmless", "defend",
        "indemnitor", "indemnitee",
    ],
    "CONFIDENTIALITY": [
        "confidential", "confidentiality", "non-disclosure", "trade secret",
        "proprietary information",
    ],
    "PAYMENT": [
        "payment", "invoice", "fee", "fees", "shall pay", "due and payable",
        "late payment", "interest at the rate", "non-refundable",
    ],
    "INTELLECTUAL_PROPERTY": [
        "intellectual property", "copyright", "patent", "trademark",
        "work for hire", "moral rights",
    ],
    "GOVERNING_LAW": [
        "governed by the laws", "governing law", "jurisdiction of the courts",
        "exclusive jurisdiction",
    ],
    "DISPUTE_RESOLUTION": [
        "arbitration", "binding arbitration", "dispute resolution", "mediation",
        "waive any right to a jury",
    ],
    "DEFINITIONS": ["means:", "shall mean", "definitions", "for purposes of this"],
    "WARRANTY": [
        "warrant", "warranty", "as is", "without warranties", "merchantability",
        "fitness for a particular purpose",
    ],
}


def _classify_with_keywords(text: str, include_top_k: int) -> Classification:
    lower = text.lower()
    scores: dict[ClassificationLabel, float] = {}

    for label, keywords in _KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in lower)
        if hits > 0:
            density = hits / max(len(text.split()), 10)
            scores[label] = min(0.95, 0.5 + density * 8)

    if not scores:
        return Classification(
            label="OTHER",
            confidence=0.55,
            top_k=[
                TopK(label="OTHER", score=0.55),
                TopK(label="DEFINITIONS", score=0.20),
                TopK(label="PAYMENT", score=0.10),
            ][:include_top_k],
        )

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_label, top_score = sorted_scores[0]

    top_k_list: list[TopK] = [TopK(label=lbl, score=round(s, 3)) for lbl, s in sorted_scores]
    while len(top_k_list) < include_top_k:
        pad_score = 0.05 / (len(top_k_list) + 1)
        top_k_list.append(TopK(label="OTHER", score=round(pad_score, 3)))
    top_k_list = top_k_list[:include_top_k]

    return Classification(
        label=top_label,
        confidence=round(top_score, 3),
        top_k=top_k_list,
    )


# -----------------------------------------------------------------------------
# Pre-compiled regex used by other pipeline modules to detect numeric durations.
# -----------------------------------------------------------------------------

NOTICE_DAYS_RE = re.compile(
    r"(?:within|upon|at\s+least|not\s+less\s+than|no\s+less\s+than|after|of)?\s*"
    r"(?:thirty\s*\(30\)|sixty\s*\(60\)|ninety\s*\(90\)|fifteen\s*\(15\)|"
    r"seven\s*\(7\)|ten\s*\(10\)|"
    r"(\d+))\s*(?:days?|day)",
    re.IGNORECASE,
)
