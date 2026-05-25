# AI Legal Intent Rewriter

## What this project is
A multi-stage NLP pipeline that ingests legal documents (PDF/text), segments them
into clauses, classifies clause type, extracts named entities, generates plain-language
rewrites, and flags risky clauses. BTech CSE final year project.

See @docs/architecture.md for the system design.
See @docs/api-contract.md for the JSON contract between web and ml services.

## Repository map
This is an npm workspaces monorepo with two deployable apps:

- `apps/web/`   — Next.js 15 (App Router, TypeScript, Tailwind, MongoDB via Mongoose).
                  Deployed to Vercel. Owns: UI, auth, file upload, DB, orchestration.
                  Has its own CLAUDE.md.
- `apps/ml/`    — Python 3.11 FastAPI service (Hugging Face Transformers, spaCy, PyMuPDF).
                  Deployed to Hugging Face Spaces (Docker SDK).
                  Owns: PDF/OCR ingestion, segmentation, classification, NER, rewriting,
                  risk flagging.
                  Has its own CLAUDE.md.
- `training/`   — Jupyter notebooks for model fine-tuning (run on Kaggle, not locally).
- `docs/`       — Architecture, API contract, evaluation reports.
- `data/`       — Gitignored except for `data/samples/` (small examples for tests).

## Tech stack at a glance
- Web: Next.js 15, TypeScript, Tailwind, shadcn/ui, MongoDB Atlas, Mongoose 8, Auth.js v5
- ML:  Python 3.11, FastAPI, PyTorch, transformers, spaCy 3.7, PyMuPDF, pytesseract
- Models: nlpaueb/legal-bert-base-uncased, google/flan-t5-small (fine-tuned on CUAD)
- Hosting: Vercel (web), Hugging Face Spaces (ml), MongoDB Atlas M0 (db)

## Conventions (apply everywhere)
- Use UK / Australian English in all user-facing copy and docs.
- Never commit secrets. Use `.env.local` for web, `.env` for ml. Both are gitignored.
- Conventional commits: `feat(ml): add risk-flag scoring`, not `update stuff`.
- Branch naming: `feat/<scope>`, `fix/<scope>`, `chore/<scope>`.
- Never push to `main` directly. Always open a PR.
- One commit per file when making multiple changes.

## Running things
- `npm run dev`                                       → starts Next.js web at :3000
- `npm run build --workspace web`                     → production build of web
- `cd apps/ml && uv run uvicorn app.main:app --reload`→ starts FastAPI at :8000
- `npm run lint --workspace web`                      → ESLint on apps/web
- `cd apps/ml && uv run pytest`                       → pytest on apps/ml

## Things to NOT do
- Don't put ML inference code in `apps/web`. The Next.js app talks to `apps/ml` over HTTP only.
- Don't commit datasets larger than 1 MB. Use HF Datasets instead.
- Don't store PDF binaries in MongoDB. Persist `extractedText` only.
- Don't add Redis, Celery, or PostgreSQL. We deliberately don't need them at this scale.
- Don't bypass plan mode for changes that touch >3 files. Ask first, code second.

## When in doubt
Read @docs/architecture.md first. The full implementation plan lives in
`docs/AI_Legal_Intent_Rewriter_Implementation_Plan.docx` (drop your copy in there).
