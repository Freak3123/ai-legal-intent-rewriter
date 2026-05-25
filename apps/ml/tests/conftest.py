"""Shared pytest fixtures."""

from __future__ import annotations

import os
from collections.abc import Iterator

# Keep tests hermetic: never touch the HF Hub or spaCy auto-download. The fallback
# chain (sklearn pickle → keyword heuristic; regex-only NER) is what unit tests verify.
os.environ.setdefault("LEGAL_REWRITER_DISABLE_HF", "1")
os.environ.setdefault("LEGAL_REWRITER_DISABLE_SPACY", "1")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    """A TestClient bound to the FastAPI app.

    Uses the context-manager form so the lifespan startup hook runs (which
    populates `_state["models_loaded"]`).
    """
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_contract_text() -> str:
    """A small but realistic 5-clause contract sample."""
    return """1. Term and Termination. This Agreement shall commence on the Effective Date \
and continue for an initial term of one (1) year, automatically renewing for successive \
one-year periods unless either party provides written notice of termination at least \
seven (7) days prior to the end of the then-current term.

2. Liability. In no event shall either party be liable to the other for any indirect, \
incidental, special, consequential, or punitive damages, including without limitation \
loss of profits, data, or use, arising out of or in connection with this Agreement.

3. Indemnification. The Customer agrees to indemnify, defend, and hold harmless the \
Company from and against any and all claims, damages, liabilities, costs, and expenses \
arising out of the Customer's use of the services.

4. Confidentiality. Each party shall maintain the confidentiality of the other party's \
Confidential Information using at least reasonable care, and shall not disclose such \
information to any third party without prior written consent.

5. Payment. Customer shall pay all undisputed invoices within thirty (30) days of \
receipt. Late payments shall accrue interest at one and one-half percent (1.5%) per \
month."""
