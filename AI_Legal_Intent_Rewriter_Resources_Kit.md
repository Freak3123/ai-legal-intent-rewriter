# AI Legal Intent Rewriter — Development Resources Kit

A practical "get started" checklist tailored for a team using **Claude Code Max**. Everything here is free or already covered by Claude Code Max — no additional spend required to follow this document.

Work through the sections in order on Day 1. Sections marked **(Week 1)** are fine to defer until later in the first week.

---

## 1. Accounts to Create

All free. Sign up with team-shared credentials where noted, so checkpoints, models, and clusters survive any single team member dropping off.

| Service | Purpose | Notes |
|---|---|---|
| **GitHub** | Code hosting, issues, CI/CD | Create a **GitHub Organisation** for the team. Free for public repos. |
| **MongoDB Atlas** | Database (free M0 tier, 512 MB) | Sign up at https://www.mongodb.com/cloud/atlas/register — pick **AWS Mumbai (ap-south-1)** region |
| **Vercel** | Next.js hosting (free Hobby tier) | Sign up with GitHub at https://vercel.com/signup |
| **Hugging Face** | Model + dataset hosting; ML service hosting (Spaces) | Sign up at https://huggingface.co/join — then **create an organisation** for the team |
| **Kaggle** | Free GPU notebooks (30 hrs/week, T4 x2) | Sign up at https://www.kaggle.com — verify phone number to unlock GPU access. Use T4 x2 as the accelerator; the current Kaggle PyTorch build crashes on P100 with a CUDA kernel-image error |
| **Google Colab** | Backup free GPU (T4) | Just needs a Google account — https://colab.research.google.com |
| **Weights & Biases** | Experiment tracking for model training | Free academic plan at https://wandb.ai — sign up with your `.ac.in` university email |

**Tip:** Use a **shared team Google account** for Kaggle, Colab, and W&B so training runs are continuous if one member is unavailable.

---

## 2. Local Tools to Install

### 2.1 Required for everyone on the team

| Tool | Why | Install |
|---|---|---|
| **Git** | Version control | `sudo apt install git` (Linux) / `brew install git` (Mac) / https://git-scm.com (Windows) |
| **GitHub CLI (`gh`)** | Claude Code uses this for issues/PRs without rate limits | https://cli.github.com — then `gh auth login` |
| **Node.js 20 LTS** | Next.js, docx tooling, JS scripts. Bundles **npm 10+** (the package manager this repo uses via npm workspaces). | Use **fnm** (https://github.com/Schniz/fnm) or **nvm** (https://github.com/nvm-sh/nvm), then `fnm install 20 && fnm use 20` |
| **Python 3.11** | FastAPI service, training notebooks (project pins `>=3.11,<3.13`) | Easiest: let **uv** (next row) fetch it on first `uv sync`. Or use **pyenv** (https://github.com/pyenv/pyenv): `pyenv install 3.11 && pyenv global 3.11` |
| **uv** | Fast Python package manager (replaces pip) | `curl -LsSf https://astral.sh/uv/install.sh \| sh` — see https://docs.astral.sh/uv/ |
| **Docker Desktop** | Required for HF Spaces deployment, optional for local dev | https://www.docker.com/products/docker-desktop |
| **Claude Code** | The whole point | See section 3 below |

### 2.2 Required for the ML lead specifically

| Tool | Why | Install |
|---|---|---|
| **Tesseract OCR** | OCR for scanned PDFs (Python wrapper calls this binary) | `sudo apt install tesseract-ocr` / `brew install tesseract` / Windows installer at https://github.com/UB-Mannheim/tesseract/wiki |
| **MongoDB Compass** | GUI for inspecting your database (highly recommended) | https://www.mongodb.com/products/compass — free |
| **Postman** or **Bruno** | Testing the FastAPI endpoints | Bruno is open-source and lighter: https://www.usebruno.com |

### 2.3 Editor (your choice)

Claude Code is a terminal tool, so the editor is up to you. Common picks:
- **VS Code** with the Claude Code extension (https://code.visualstudio.com)
- **Cursor** (https://cursor.com) — also works with Claude Code in its terminal
- **Vim / Neovim** if that's your thing

---

## 3. Claude Code Setup

You have Claude Code Max, so you're sorted on the cost side. Below is the install + first-session setup.

### 3.1 Install

The native installer is the official path as of 2026 (no Node.js required):

```bash
# macOS / Linux
curl -fsSL https://claude.ai/install.sh | bash

# Windows (PowerShell)
irm https://claude.ai/install.ps1 | iex
```

Verify:
```bash
claude --version
```

Reference: https://docs.claude.com/en/docs/claude-code/overview

### 3.2 First-time configuration

Once installed:

```bash
cd /path/to/your/project
claude        # opens the interactive session
```

Inside the session, run these one-time setup commands:

| Command | What it does |
|---|---|
| `/login` | Authenticate with your Anthropic account |
| `/init` | Auto-generates a starter `CLAUDE.md` from your project structure (run this AFTER you scaffold the monorepo, then merge with the template in section 6) |
| `/model` | Pick the default model — for this project, use **Opus** for planning and **Sonnet** for routine code |
| `/context` | See current context window usage |
| `/usage` | Check Max plan limits (so you know when you're approaching them) |
| `/config` | Open the settings panel |

### 3.3 MCP servers worth adding

MCP (Model Context Protocol) servers let Claude Code talk to external tools directly. For this project, two are very high-value:

**MongoDB MCP** — lets Claude inspect, query, and modify your Atlas data during development. Massively useful when debugging analyses or schema issues.

```bash
claude mcp add mongodb \
  --transport stdio \
  -- npx -y mongodb-mcp-server \
  --connectionString "your-atlas-connection-string"
```
Reference: https://www.mongodb.com/docs/mcp-server/

**Hugging Face MCP** — lets Claude browse models/datasets, check Space build logs, and pull model cards without you copy-pasting URLs.

```bash
claude mcp add huggingface --transport http https://hf.co/mcp
```

To list / remove MCP servers later:
```bash
claude mcp list
claude mcp remove <name>
```

### 3.4 Workflow practices to adopt from Day 1

- **Plan mode (Shift+Tab)** — toggles into a read-only "show me what you'd do" mode. Use it before any change that touches multiple files or runs migrations.
- **Explore → Plan → Implement → Commit** — Anthropic's recommended flow. Resist "build me feature X" on the first prompt; ask Claude to read the code first.
- **One commit per file** when Claude is making multiple changes — keeps your git history reviewable.
- **Use feature branches** for all Claude-driven work: `git checkout -b feat/clause-classifier`.

---

## 4. Datasets to Download (Week 1)

All free. Most are on the Hugging Face Hub or GitHub.

| Dataset | Size | Source | Use for |
|---|---|---|---|
| **CUAD** | 510 contracts, 13K+ annotations | https://huggingface.co/datasets/theatticusproject/cuad-qa | **Primary** clause classification training data |
| **LEDGAR** | ~1M provisions from SEC filings | https://huggingface.co/datasets/lex_glue (subset `ledgar`) | Supplementary classification training |
| **UNFAIR-ToS** | 100 ToS docs with unfair-clause labels | https://huggingface.co/datasets/lex_glue (subset `unfair_tos`) | Risk-flagging calibration |
| **ContractNLI** | 607 contracts, NLI hypotheses | https://stanfordnlp.github.io/contract-nli/ | Optional: NER + clause understanding |
| **LexGLUE** (full) | 7-task benchmark | https://huggingface.co/datasets/lex_glue | Benchmarking the classifier |
| **Plain English Contracts** | ~440 (legal, plain) pairs | https://github.com/lauramanor/legal_summarization | **Primary** training data for FLAN-T5 simplification |
| **MultiLegalPile** (optional) | Large multilingual legal corpus | https://huggingface.co/datasets/joelniklaus/MultiLegalPile_Wikipedia_Filtered | Domain pre-training (only if you have budget) |

Quick CUAD download via Python:
```python
from datasets import load_dataset
ds = load_dataset("theatticusproject/cuad-qa")
print(ds)
```

Push your processed/combined dataset to your team's HF org so it's versioned:
```python
ds.push_to_hub("your-team/legal-clauses-v1")
```

---

## 5. Pre-trained Models You'll Pull

These all download automatically the first time `transformers.from_pretrained()` is called — but it's worth knowing what they are and where they live.

| Model | Hub ID | Size | Role |
|---|---|---|---|
| **Legal-BERT (uncased)** | `nlpaueb/legal-bert-base-uncased` | 420 MB | Primary clause classifier |
| **DistilBERT** | `distilbert-base-uncased` | 250 MB | Fallback classifier (faster, smaller) |
| **FLAN-T5 Small** | `google/flan-t5-small` | 300 MB | Primary clause-rewriting model |
| **BART base** | `facebook/bart-base` | 560 MB | Alternative seq2seq rewriter |
| **spaCy `en_core_web_lg`** | spaCy direct | 750 MB | NER backbone | 
| **spaCy `en_core_web_trf`** | spaCy direct | 440 MB | Transformer NER (heavier, more accurate) |

spaCy models install differently:
```bash
python -m spacy download en_core_web_lg
```

Reference: https://huggingface.co/models?other=legal

---

## 6. CLAUDE.md Templates

Drop these into your repo so every Claude Code session starts with the right context. **Keep them under ~150 lines each** — bloated CLAUDE.md files get ignored.

### 6.1 Root `CLAUDE.md`

```markdown
# AI Legal Intent Rewriter

## What this project is
A multi-stage NLP pipeline that ingests legal documents (PDF/text), segments them
into clauses, classifies clause type, extracts named entities, generates plain-language
rewrites, and flags risky clauses. BTech CSE final year project.

See @docs/architecture.md for the full system design.
See @docs/api-contract.md for the JSON contract between web and ml services.

## Repository map
This is an npm workspaces monorepo with two deployable apps:

- `apps/web/`   — Next.js 15 (App Router, TypeScript, Tailwind, MongoDB via Mongoose)
                  Deployed to Vercel. Owns: UI, auth, file upload, DB, orchestration.
                  Has its own CLAUDE.md.
- `apps/ml/`    — Python FastAPI service (Hugging Face Transformers, spaCy, PyMuPDF)
                  Deployed to Hugging Face Spaces (Docker SDK).
                  Owns: PDF/OCR ingestion, segmentation, classification, NER, rewriting,
                  risk flagging.
                  Has its own CLAUDE.md.
- `training/`   — Jupyter notebooks for model fine-tuning (run on Kaggle, not locally).
- `data/`       — Gitignored except for small samples in `data/samples/`.
- `docs/`       — Architecture, API contract, evaluation reports.

## Tech stack at a glance
- Web: Next.js 14, TypeScript, Tailwind, shadcn/ui, MongoDB Atlas, Mongoose, NextAuth
- ML:  Python 3.11, FastAPI, PyTorch, transformers, spaCy, PyMuPDF, pytesseract
- Models: nlpaueb/legal-bert-base-uncased, google/flan-t5-small (fine-tuned on CUAD)
- Hosting: Vercel (web), Hugging Face Spaces (ml), MongoDB Atlas M0 (db)

## Conventions (apply everywhere)
- Use UK / Australian English in all user-facing copy and docs (colour, organisation, etc.)
- Never commit secrets. Use `.env.local` for web, `.env` for ml. Both are gitignored.
- One commit per file when making multiple changes.
- Branch naming: `feat/<scope>`, `fix/<scope>`, `chore/<scope>`.
- Conventional commits: `feat(ml): add risk-flag scoring`, not `update stuff`.
- Never push to `main` directly. Always open a PR.

## Running things
- `npm run dev`                                       → starts Next.js web at http://localhost:3000
- `npm run build --workspace web`                     → production build of web
- `cd apps/ml && uv run uvicorn app.main:app --reload`→ starts FastAPI at :8000
- `npm run lint --workspace web`                      → ESLint on apps/web
- `cd apps/ml && uv run pytest`                       → tests on apps/ml

## Things to NOT do
- Don't put ML inference code in apps/web. The Next.js app talks to apps/ml over HTTP only.
- Don't commit datasets larger than 1 MB. Use HF Datasets instead.
- Don't store PDF binaries in MongoDB. Persist `extractedText` only.
- Don't add Redis, Celery, or PostgreSQL. We deliberately don't need them at this scale.
- Don't bypass plan mode for changes that touch >3 files. Ask first, code second.

## When in doubt
Read @docs/architecture.md first. The full implementation plan lives in
@docs/AI_Legal_Intent_Rewriter_Implementation_Plan.docx — refer to it for any
question about why a decision was made.
```

### 6.2 `apps/web/CLAUDE.md`

```markdown
# apps/web — Next.js Application

This is the Next.js 14 App Router project. UI, auth, MongoDB persistence, orchestration.

## Architecture
- App Router (no pages directory)
- Server Components by default; `"use client"` only when needed for interactivity
- Database access via Mongoose, only inside server components / route handlers
- Calls the FastAPI ML service over HTTP using `lib/ml-client.ts`

## Folder map
- `app/(auth)/`        — login/signup UI
- `app/dashboard/`     — list of analyses, detailed clause view
- `app/upload/`        — drag-and-drop UI
- `app/api/`           — REST routes (auth, documents, analyses)
- `components/ui/`     — shadcn primitives (don't edit, just compose)
- `components/`        — feature components (ClauseCard, RiskBadge, SideBySide, etc.)
- `lib/db/models/`     — Mongoose schemas (one file per collection)
- `lib/ml-client.ts`   — typed client for FastAPI; SOURCE OF TRUTH for response types
- `types/`             — shared types mirroring FastAPI pydantic schemas

## Conventions
- TypeScript strict mode. No `any`. No `@ts-ignore` without an inline reason.
- Validate all API inputs with zod. Reuse schemas in client forms.
- Use TanStack Query for any data that's fetched after page load.
- Tailwind for styling. No CSS modules, no styled-components.
- Mongoose: use `mongoose.connect()` singleton in `lib/db/mongoose.ts`. Never reconnect per request.

## Commands
- `npm run dev`        → dev server on :3000
- `npm run build`      → production build (run before merging to main)
- `npm run lint`       → ESLint
- `npm run typecheck`  → tsc --noEmit
- `npm run format`     → Prettier

## When adding a new MongoDB field
1. Update the Mongoose schema in `lib/db/models/`
2. Update the matching TypeScript type in `types/`
3. Update any zod schema that validates user input for it
4. If the field is in API responses, update `docs/api-contract.md`
```

### 6.3 `apps/ml/CLAUDE.md`

```markdown
# apps/ml — FastAPI ML Service

Python 3.11 + FastAPI service. Deployed to Hugging Face Spaces (Docker SDK).
ALL NLP / ML inference for the project lives here. The Next.js app calls this
service over HTTP — never the other way round.

## Folder map
- `app/main.py`             — FastAPI app, CORS, route mounting
- `app/pipeline/ingest.py`  — PyMuPDF for digital PDFs, pytesseract for scanned
- `app/pipeline/segment.py` — Rule-based + spaCy clause segmentation
- `app/pipeline/classify.py`— Legal-BERT inference (loads from HF Hub on cold start)
- `app/pipeline/ner.py`     — spaCy + EntityRuler patterns
- `app/pipeline/rewrite.py` — FLAN-T5-small inference
- `app/pipeline/risk.py`    — Rule-based risk scoring (3 layers — see docstring)
- `app/schemas/`            — pydantic request/response models
- `app/config.py`           — Model IDs, thresholds, env-driven settings

## Conventions
- All public model IDs pinned in `config.py` with semver tag (e.g., `team/legal-bert-cuad-v1`)
- Models loaded ONCE at app startup, cached in memory (Spaces gives 16 GB)
- Async route handlers; sync inference is fine inside them (PyTorch is blocking anyway)
- Type hints everywhere. Use pydantic for all data structures crossing module boundaries.
- Format with `ruff format`. Lint with `ruff check`.
- Tests with pytest. Cover the pipeline modules; mock the model calls.

## Commands
- `uv sync`                                     → install deps from pyproject.toml
- `uv run uvicorn app.main:app --reload`        → dev server at :8000
- `uv run pytest`                               → tests
- `uv run ruff check . && uv run ruff format .` → lint + format
- `docker build -t legal-rewriter-ml .`         → builds the HF Spaces image

## Adding a new pipeline component
1. Create `app/pipeline/<name>.py` with a single public function
2. Add pydantic input/output schemas in `app/schemas/`
3. Wire it into `app/main.py`'s `/v1/analyze` handler
4. Add a test in `tests/test_<name>.py` with fixtures, not real model loads
5. Update `docs/api-contract.md` if the response shape changed

## Models
We pin specific model versions. Bump them by:
1. Pushing the new fine-tuned checkpoint to HF Hub from a Kaggle notebook
2. Updating ONE line in `config.py`
3. Restarting the Space (`huggingface-cli space restart <name>`)

## DO NOT
- Don't `transformers.pipeline()` — too much overhead. Use the model + tokenizer directly.
- Don't load models inside route handlers. Load at startup in `app.main:app`.
- Don't trust client-supplied text length. Cap clauses at 5,000 chars.
- Don't store anything to disk except the model cache.
```

---

## 7. Documentation to Bookmark

Keep these tabs handy. Reading them once before you start each component will save you days.

### 7.1 Frontend / Web stack
- Next.js 14 App Router — https://nextjs.org/docs
- TypeScript Handbook — https://www.typescriptlang.org/docs/handbook/
- Tailwind CSS — https://tailwindcss.com/docs
- shadcn/ui — https://ui.shadcn.com/docs
- TanStack Query — https://tanstack.com/query/latest/docs
- NextAuth (Auth.js v5) — https://authjs.dev
- react-hook-form — https://react-hook-form.com
- zod — https://zod.dev
- pdf.js — https://mozilla.github.io/pdf.js/

### 7.2 Database
- MongoDB Atlas getting started — https://www.mongodb.com/docs/atlas/getting-started/
- Mongoose docs — https://mongoosejs.com/docs/
- MongoDB schema design patterns — https://www.mongodb.com/developer/products/mongodb/schema-design-anti-pattern-summary/

### 7.3 ML / Backend
- FastAPI — https://fastapi.tiangolo.com
- Hugging Face Transformers — https://huggingface.co/docs/transformers
- Hugging Face NLP Course (free) — https://huggingface.co/learn/nlp-course
- spaCy 3 — https://spacy.io/usage
- PyMuPDF — https://pymupdf.readthedocs.io
- pytesseract — https://github.com/madmaze/pytesseract

### 7.4 Training & evaluation
- HF Trainer API — https://huggingface.co/docs/transformers/main_classes/trainer
- HF Datasets — https://huggingface.co/docs/datasets
- Fine-tune Legal-BERT walkthrough — https://huggingface.co/blog/legal-bert
- Weights & Biases quickstart — https://docs.wandb.ai/quickstart
- Kaggle GPU notebooks guide — https://www.kaggle.com/docs/notebooks
- sacrebleu — https://github.com/mjpost/sacrebleu
- rouge-score — https://github.com/google-research/google-research/tree/master/rouge

### 7.5 Deployment
- Vercel (Next.js deploy) — https://vercel.com/docs/frameworks/nextjs
- HF Spaces (Docker SDK) — https://huggingface.co/docs/hub/spaces-sdks-docker
- HF Spaces secrets management — https://huggingface.co/docs/hub/spaces-overview#managing-secrets
- MongoDB Atlas IP allowlisting — https://www.mongodb.com/docs/atlas/security/ip-access-list/

### 7.6 Claude Code
- Overview — https://docs.claude.com/en/docs/claude-code/overview
- Best practices — https://code.claude.com/docs/en/best-practices
- MCP server config — https://docs.claude.com/en/docs/claude-code/mcp
- Slash commands — https://docs.claude.com/en/docs/claude-code/slash-commands
- Plan mode — https://docs.claude.com/en/docs/claude-code/plan-mode

---

## 8. Learning Resources (if you've not done this before)

Honest assessment: if anyone on the team is new to a part of this stack, work through one of these *before* you try to ship it with Claude Code. AI assistance accelerates people who already understand the basics; it amplifies confusion for those who don't.

| If you're new to... | Best free resource (do this first) |
|---|---|
| Next.js App Router | Official Next.js Learn course — https://nextjs.org/learn (4 hours) |
| MongoDB | M001 Basics on MongoDB University — https://learn.mongodb.com/courses/m001-mongodb-basics (free, 8 hours) |
| Hugging Face / fine-tuning | HF NLP Course chapters 1-3 — https://huggingface.co/learn/nlp-course (6 hours) |
| FastAPI | Official tutorial — https://fastapi.tiangolo.com/tutorial/ (3 hours) |
| Transformers / BERT | The Illustrated BERT — https://jalammar.github.io/illustrated-bert/ (1 hour read) |
| Tailwind / shadcn/ui | Build a project from a YouTube tutorial — search "shadcn next.js tutorial" for your level |

---

## 9. Day 1 Checklist

Tick these off in this order. With Claude Code helping, this is a 4-6 hour session, not a full day.

```
[ ] Sign up for GitHub, MongoDB Atlas, Vercel, Hugging Face, Kaggle, Weights & Biases
[ ] Create a GitHub Organisation and a Hugging Face Organisation for the team
[ ] Install: git, gh, Node 20 (via fnm/nvm) — npm comes bundled, Python 3.11 (or let uv fetch it), uv, Docker
[ ] Install Tesseract OCR (ML lead only)
[ ] Install Claude Code (curl one-liner)
[ ] Run `claude` in an empty folder, then `/login`
[ ] Create the monorepo structure (let Claude Code scaffold it from the impl plan)
[ ] Add the three CLAUDE.md files from section 6 of this doc
[ ] Add MongoDB MCP and Hugging Face MCP to Claude Code (section 3.3)
[ ] Create MongoDB Atlas M0 cluster in AWS Mumbai region; whitelist 0.0.0.0/0
[ ] Push empty repo to GitHub; connect Vercel for auto-deploy
[ ] Deploy an empty FastAPI Space on Hugging Face (Docker SDK)
[ ] First end-to-end smoke test: browser → Vercel-hosted Next.js → HF Space → returns "ok"
```

If you finish all this on Day 1, you're already a week ahead of where most teams start.

---

## 10. What to Ask Claude Code for First

Once you have the repo scaffolded and Claude Code running with `CLAUDE.md` in place, here are good first prompts (in order):

1. **"Read the implementation plan in `@docs/AI_Legal_Intent_Rewriter_Implementation_Plan.docx` and give me a summary of what we're building. Don't write any code yet."** — gets Claude oriented.

2. **"Set up `apps/web` as a Next.js 14 App Router project with TypeScript, Tailwind, shadcn/ui, NextAuth, and Mongoose. Match the folder structure described in the implementation plan section 4. Use plan mode."** — Shift+Tab into plan mode first.

3. **"Set up `apps/ml` as a FastAPI service with the folder structure from section 4 of the impl plan. Add a `/v1/health` endpoint and a stub `/v1/analyze` that returns mock data matching the API contract in section 6. Use uv for dependency management."**

4. **"Create the Mongoose models for `users`, `documents`, `analyses`, `clauses` per section 5 of the impl plan. Add the indexes from section 5.5. Include zod schemas for the matching API request bodies."**

5. **"Wire up the Next.js `/api/analyses` POST route to call the FastAPI `/v1/analyze` endpoint, save the result to MongoDB, and return the analysis ID."**

After step 5, you have a working stub end-to-end. Everything from there is replacing stubs with real implementations.

---

## 11. Useful Commands Cheat Sheet

```bash
# Project bootstrap (already done — kept for reference)
npm init -y
npm install -D typescript @types/node
npx create-next-app@latest apps/web --typescript --tailwind --app --src-dir=false

# Add shadcn
cd apps/web && npx shadcn@latest init

# FastAPI scaffold
cd apps/ml && uv init && uv add fastapi uvicorn[standard] pydantic transformers torch spacy pymupdf pytesseract

# spaCy model
uv run python -m spacy download en_core_web_lg

# Run everything in dev (in 2 terminals)
npm run dev                                         # terminal 1: Next.js
cd apps/ml && uv run uvicorn app.main:app --reload  # terminal 2: FastAPI

# Push a fine-tuned model to HF Hub
huggingface-cli login
# In your training notebook:
#   model.push_to_hub("your-team/legal-bert-cuad-v1")
#   tokenizer.push_to_hub("your-team/legal-bert-cuad-v1")

# Deploy to HF Spaces (after setting up the Space)
git remote add space https://huggingface.co/spaces/your-team/legal-rewriter-ml
git push space main

# Vercel deploy (after connecting GitHub repo, this is automatic on push to main)
git push origin main
```

---

## 12. When You Get Stuck

In rough order of who/what to ask:

1. **Claude Code itself** — the answer is usually in your codebase or docs already. `"Why is my MongoDB connection timing out?"` works.
2. **The impl plan doc** — `docs/AI_Legal_Intent_Rewriter_Implementation_Plan.docx` covers the *why* of every architectural decision.
3. **Official docs** for the specific tool (section 7 of this doc).
4. **GitHub Issues** for the specific library — search before posting.
5. **Stack Overflow / Hugging Face Forums** — for ML-specific debugging, the HF forums are far better than SO.
6. **Your supervisor / project coordinator** — for scope, evaluation, and submission questions.

Do not paste large chunks of code into ChatGPT or other LLMs while working on this — keep the workflow inside Claude Code so the context stays consistent.

---

*— End of resources kit —*
