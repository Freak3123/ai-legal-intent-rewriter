"""Tests for the TF-IDF baseline classifier."""

from __future__ import annotations

from typing import get_args

from app.pipeline.classify import _load_sklearn_model, classify_clause
from app.schemas import ClassificationLabel

VALID_LABELS = set(get_args(ClassificationLabel))


def test_sklearn_artifact_loads() -> None:
    """The trained sklearn fallback artifact should be on disk and loadable."""
    model = _load_sklearn_model()
    assert model is not None, "clause_classifier.pkl missing — run scripts/train_classifier.py"


def test_returns_valid_label() -> None:
    result = classify_clause(
        "Either party may terminate this Agreement upon thirty (30) days written notice."
    )
    assert result.label in VALID_LABELS


def test_confidence_in_range() -> None:
    result = classify_clause("Customer shall pay invoices within thirty days of receipt.")
    assert 0.0 <= result.confidence <= 1.0


def test_top_k_respects_include_top_k() -> None:
    result = classify_clause(
        "In no event shall either party be liable for indirect damages.",
        include_top_k=5,
    )
    assert 1 <= len(result.top_k) <= 5
    # All items must be valid labels
    for entry in result.top_k:
        assert entry.label in VALID_LABELS
        assert 0.0 <= entry.score <= 1.0


def test_top_k_is_sorted_descending() -> None:
    result = classify_clause(
        "The Customer agrees to indemnify, defend, and hold harmless the Company.",
        include_top_k=5,
    )
    scores = [t.score for t in result.top_k]
    assert scores == sorted(scores, reverse=True)


def test_top_label_matches_first_top_k_entry() -> None:
    result = classify_clause("This Agreement shall be governed by the laws of Delaware.")
    assert result.top_k[0].label == result.label
    assert abs(result.top_k[0].score - result.confidence) < 1e-6


def test_termination_clause_classified_plausibly() -> None:
    """A canonical termination clause should land in TERMINATION or RENEWAL,
    both of which are about contract end-of-life. Loose check on purpose.

    We avoid sentences with embedded notice periods (e.g. "thirty days") since
    those overlap heavily with PAYMENT under the bag-of-words baseline.
    """
    result = classify_clause(
        "Either party may terminate this Agreement for cause if the other party "
        "becomes insolvent or ceases to do business in the ordinary course."
    )
    assert result.label in {"TERMINATION", "RENEWAL"}


def test_payment_clause_classified_plausibly() -> None:
    result = classify_clause(
        "Customer shall pay all undisputed invoices within thirty days of receipt and "
        "late payments shall accrue interest at one and one-half percent per month."
    )
    assert result.label == "PAYMENT"
