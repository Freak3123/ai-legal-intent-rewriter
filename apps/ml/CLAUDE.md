# apps/ml — FastAPI ML Service

Python 3.11 + FastAPI service. Deployed to Hugging Face Spaces (Docker SDK).
ALL NLP / ML inference for the project lives here. The Next.js app calls this
service over HTTP — never the other way round.

## Folder map
- `app/main.py`             — FastAPI app, CORS, route mounting, model loading at startup
- `app/config.py`           — Model IDs (pinned), thresholds, env-driven settings
- `app/pipeline/ingest.py`  — PyMuPDF for digital PDFs, pytesseract for scanned (stub)
- `app/pipeline/segment.py` — Rule-based + spaCy clause segmentation (stub)
- `app/pipeline/classify.py`— Legal-BERT inference (stub returning OTHER for now)
- `app/pipeline/ner.py`     — spaCy + EntityRuler patterns (stub)
- `app/pipeline/rewrite.py` — FLAN-T5-small inference (stub returning truncated original)
- `app/pipeline/risk.py`    — Rule-based risk scoring; 3 layers (keyword, regex, heuristic)
- `app/schemas/`            — pydantic request/response models, mirror @docs/api-contract.md
- `tests/`                  — pytest suite

## Conventions
- All public model IDs pinned in `config.py` with a semver tag (e.g., `team/legal-bert-cuad-v1`)
- Models loaded ONCE at app startup, cached in memory (Spaces gives 16 GB)
- Async route handlers; sync inference is fine inside them (PyTorch is blocking anyway)
- Type hints everywhere. Use pydantic for all data structures crossing module boundaries.
- Format with `ruff format`. Lint with `ruff check`.

## Commands
- `uv sync`                                     → install deps from pyproject.toml
- `uv run uvicorn app.main:app --reload`        → dev server at :8000
- `uv run pytest`                               → tests
- `uv run ruff check . && uv run ruff format .` → lint + format
- `docker build -t legal-rewriter-ml .`         → builds the HF Spaces image
- `docker run -p 8000:7860 legal-rewriter-ml`   → run the Docker image locally

## Replacing a stub with real implementation
1. Find the stub in `app/pipeline/<name>.py` — look for the `# STUB` comment
2. Replace the stub function body with a real implementation
3. If you need a new model, pin it in `config.py`
4. Update tests in `tests/test_<name>.py`
5. Don't change the function signature — `app/main.py` depends on it

## Adding a new pipeline component
1. Create `app/pipeline/<name>.py` with a single public function
2. Add pydantic input/output shapes in `app/schemas/`
3. Wire it into `app/main.py`'s `/v1/analyze` handler
4. Add a test in `tests/test_<name>.py` with fixtures, not real model loads
5. Update `@docs/api-contract.md` if the response shape changed

## DO NOT
- Don't `transformers.pipeline()` — too much overhead. Use the model + tokenizer directly.
- Don't load models inside route handlers. Load at startup in `app.main:app`.
- Don't trust client-supplied text length. Cap clauses at 5,000 chars.
- Don't store anything to disk except the model cache.
- Don't use `dotenv` — Spaces injects env vars from its secrets UI.
