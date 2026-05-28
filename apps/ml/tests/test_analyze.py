"""End-to-end /v1/analyze tests against the stub implementations."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_analyze_returns_clauses(client: TestClient, sample_contract_text: str) -> None:
    response = client.post(
        "/v1/analyze",
        json={"input_type": "text", "text": sample_contract_text},
    )
    assert response.status_code == 200
    body = response.json()

    # Top-level shape
    assert body["ingestion_method"] == "text-direct"
    assert isinstance(body["clauses"], list)
    assert len(body["clauses"]) >= 4  # 5 numbered clauses, allowing some segmentation slack

    # Metrics
    assert body["metrics"]["total_clauses"] == len(body["clauses"])
    assert body["metrics"]["avg_confidence"] > 0

    # Model versions string-present
    assert "classifier" in body["model_versions"]
    assert "rewriter" in body["model_versions"]

    # Timing dict has all keys
    for k in (
        "ingestion", "segmentation", "classification",
        "ner", "rewriting", "risk_flagging", "total",
    ):
        assert k in body["timing_ms"]


def test_analyze_clause_shape(client: TestClient, sample_contract_text: str) -> None:
    response = client.post(
        "/v1/analyze",
        json={"input_type": "text", "text": sample_contract_text},
    )
    body = response.json()
    first = body["clauses"][0]

    # Required fields
    assert isinstance(first["ordinal"], int)
    assert isinstance(first["original_text"], str) and first["original_text"]
    assert "start" in first["char_span"] and "end" in first["char_span"]

    # Classification
    assert isinstance(first["classification"]["label"], str)
    assert 0.0 <= first["classification"]["confidence"] <= 1.0
    assert isinstance(first["classification"]["top_k"], list)

    # Rewrite
    assert first["rewrite"]["text"]
    assert first["rewrite"]["method"] in ("model", "template-fallback")

    # Risk
    assert first["risk"]["level"] in ("low", "medium", "high")
    assert 0.0 <= first["risk"]["score"] <= 1.0


def test_analyze_termination_flagged_high_risk(client: TestClient) -> None:
    """A 7-day notice termination clause should land in medium/high risk."""
    response = client.post(
        "/v1/analyze",
        json={
            "input_type": "text",
            "text": (
                "1. Termination. The Company may terminate this Agreement at any time "
                "without cause upon seven (7) days written notice to the Customer."
            ),
        },
    )
    body = response.json()
    first = body["clauses"][0]
    assert first["classification"]["label"] == "TERMINATION"
    # Should trip both short-notice-period and unilateral-termination
    assert "short-notice-period" in first["risk"]["triggers"]
    assert first["risk"]["level"] in ("medium", "high")


def test_analyze_rejects_empty_text(client: TestClient) -> None:
    response = client.post("/v1/analyze", json={"input_type": "text", "text": ""})
    # Pydantic validation kicks in — 422 from FastAPI
    assert response.status_code == 422


def test_analyze_extracts_amount_entities(client: TestClient) -> None:
    response = client.post(
        "/v1/analyze",
        json={
            "input_type": "text",
            "text": (
                "1. Payment. Customer shall pay $5,000 within thirty (30) days. "
                "Late payments accrue 1.5% interest per month."
            ),
        },
    )
    body = response.json()
    entities = body["clauses"][0]["entities"]
    types = {e["type"] for e in entities}
    assert "AMOUNT" in types
    assert "DATE" in types
