# AI Legal Intent Rewriter

A multi-stage NLP pipeline that ingests legal documents, segments them into clauses,
classifies each clause by type, extracts named entities, generates plain-language
rewrites, and flags potentially risky clauses.

> **BTech CSE (AIML) Final Year Project** — Siksha 'O' Anusandhan University.
> See [`docs/architecture.md`](./docs/architecture.md) for the full design.

---

## Repository layout

This is an `npm` workspaces monorepo containing two deployable apps:

| Path | What it is | Where it deploys | Stack |
|---|---|---|---|
| `apps/web/` | User-facing Next.js application | Vercel (free Hobby tier) | Next.js 15 · TypeScript · Tailwind · shadcn/ui · MongoDB · Auth.js v5 |
| `apps/ml/` | FastAPI ML inference microservice | Hugging Face Spaces (free) | Python 3.11 · FastAPI · Transformers · spaCy · PyMuPDF |
| `training/` | Jupyter notebooks for model fine-tuning | Run on Kaggle / Colab | PyTorch · Hugging Face |
| `docs/` | Architecture & API contract | — | Markdown |

---

## Quick start (10 minutes)

### 1. Prerequisites

- Node.js 20+ (use [`fnm`](https://github.com/Schniz/fnm) or [`nvm`](https://github.com/nvm-sh/nvm)) — bundled with npm 10+
- Python 3.11+ (use [`pyenv`](https://github.com/pyenv/pyenv))
- [`uv`](https://docs.astral.sh/uv/) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- A MongoDB Atlas connection string (free M0 tier)
- (Optional, ML lead only) Tesseract OCR — `sudo apt install tesseract-ocr` / `brew install tesseract`

### 2. Clone & install

```bash
git clone https://github.com/<your-org>/ai-legal-intent-rewriter.git
cd ai-legal-intent-rewriter

# Install JS deps for apps/web (uses npm workspaces)
npm install

# Install Python deps for apps/ml
cd apps/ml && uv sync && cd ../..
```

### 3. Configure environment

```bash
# Web
cp apps/web/.env.example apps/web/.env.local
# Edit apps/web/.env.local — set MONGODB_URI, NEXTAUTH_SECRET, ML_SERVICE_URL

# ML
cp apps/ml/.env.example apps/ml/.env
# Edit apps/ml/.env if you want to override defaults (works fine empty)
```

Generate a NextAuth secret quickly:
```bash
openssl rand -base64 32
```

### 4. Run both apps

In **two terminals**:

```bash
# Terminal 1 — Next.js on http://localhost:3000
npm run dev

# Terminal 2 — FastAPI on http://localhost:8000
cd apps/ml && uv run uvicorn app.main:app --reload
```

### 5. End-to-end smoke test

1. Open http://localhost:3000
2. Sign up for a local account
3. Go to **Upload**, drop a PDF or paste some clauses
4. Watch a mock analysis come back from the FastAPI stub
5. Click into the analysis on the dashboard to see clauses rendered

If all five steps work, the scaffold is wired correctly. Everything from here is
**replacing stubs with real implementations** — see `docs/architecture.md` for the
phase-by-phase plan.

---

## Useful commands

```bash
# Web
npm run dev                            # dev server
npm run build --workspace web          # production build
npm run lint --workspace web           # ESLint
npm run typecheck --workspace web      # TypeScript only

# ML
cd apps/ml
uv run uvicorn app.main:app --reload   # dev server
uv run pytest                          # tests
uv run ruff check .                    # lint
uv run ruff format .                   # format

# Add a shadcn component (run from apps/web)
npx shadcn@latest add dialog

# Add a Python dep (run from apps/ml)
uv add transformers

# Build the ML Docker image (for HF Spaces)
cd apps/ml && docker build -t legal-rewriter-ml .
```

---

## Working with Claude Code

This repo ships with three `CLAUDE.md` files (root, `apps/web/`, `apps/ml/`) so that
every Claude Code session starts with the right context for whichever directory
you're working in.

Set up MongoDB and Hugging Face MCP servers — they're high-leverage for this
project. See [`docs/claude-code-setup.md`](./docs/claude-code-setup.md).

---

## Deployment

| Component | Provider | How |
|---|---|---|
| `apps/web` | Vercel | Connect the GitHub repo on Vercel; set root directory to `apps/web`; add the env vars from `.env.example` |
| `apps/ml` | Hugging Face Spaces | Create a Space (Docker SDK); push `apps/ml/` to its git remote; add secrets in the Space settings |
| MongoDB | Atlas M0 | Region: AWS Mumbai (`ap-south-1`); IP allowlist: `0.0.0.0/0` |

---

## Licence

MIT — see [`LICENSE`](./LICENSE).
# ai-legal-intent-rewriter
