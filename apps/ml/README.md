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
[AI Legal Intent Rewriter](https://github.com/Freak3123/ai-legal-intent-rewriter)
project. Deployed to Hugging Face Spaces (Docker SDK, free CPU tier).

## Endpoints

- `GET /v1/health` — readiness check (use to pre-warm a sleeping Space)
- `POST /v1/analyze` — run the pipeline on text or PDF, return structured analysis
- `GET /docs` — Swagger UI (FastAPI auto-generates)

See the API contract in
[`docs/api-contract.md`](https://github.com/Freak3123/ai-legal-intent-rewriter/blob/main/docs/api-contract.md)
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

## Models

| Component | Hub ID | Metric |
|---|---|---|
| Clause classifier | [`freak3123/legal-bert-cuad-v1`](https://huggingface.co/freak3123/legal-bert-cuad-v1) | macro F1 = 0.902 on a held-out 419-clause test set |
| Clause rewriter | [`freak3123/flan-t5-simplify-v1`](https://huggingface.co/freak3123/flan-t5-simplify-v1) | validation ROUGE-L = 0.352 |
| NER | spaCy `en_core_web_sm` + restrictive regex hybrid | — |

Both transformer models are pulled from the Hub on first request and cached
under `/tmp/huggingface`. The service falls back to a TF-IDF + LogReg pickle
and a template rewriter automatically if either Hub model is unreachable.

## Endpoints in detail

- `POST /v1/analyze` — JSON body, text mode (preferred for digital PDFs the
  client has already extracted)
- `POST /v1/analyze/pdf` — multipart upload, runs PyMuPDF then Tesseract OCR
  if the text layer is empty
