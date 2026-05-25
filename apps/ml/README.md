---
title: AI Legal Intent Rewriter ML
emoji: ⚖️
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: ML inference service for the AI Legal Intent Rewriter
---

# AI Legal Intent Rewriter — ML Service

FastAPI microservice that runs the NLP pipeline for the
[AI Legal Intent Rewriter](https://github.com/your-org/ai-legal-intent-rewriter)
project. Deployed to Hugging Face Spaces (Docker SDK, free CPU tier).

## Endpoints

- `GET /v1/health` — readiness check (use to pre-warm a sleeping Space)
- `POST /v1/analyze` — run the pipeline on text or PDF, return structured analysis
- `GET /docs` — Swagger UI (FastAPI auto-generates)

See the API contract in
[`docs/api-contract.md`](https://github.com/your-org/ai-legal-intent-rewriter/blob/main/docs/api-contract.md)
in the main repo.

## Local development

```bash
# Install deps
uv sync

# Run dev server (with hot reload)
uv run uvicorn app.main:app --reload

# Run tests
uv run pytest

# Lint + format
uv run ruff check .
uv run ruff format .
```

The service runs on `:8000` locally and `:7860` inside the Docker container
(HF Spaces convention).

## Docker (mirrors HF Spaces deployment)

```bash
docker build -t legal-rewriter-ml .
docker run -p 8000:7860 legal-rewriter-ml
```

## Status

This service ships as a **stub** — every pipeline component returns mock data
matching the API contract. Replace stubs with real implementations as you
finish each phase of the project (see `app/pipeline/*.py` — look for `# STUB`
comments).
