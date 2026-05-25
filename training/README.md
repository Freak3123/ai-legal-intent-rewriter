# Training Notebooks

Jupyter notebooks for fine-tuning the project's models. Each one is meant to
run on **Kaggle** (free T4 x2, 30 hours/week) — not on your laptop.

## Notebooks

| File | Purpose | Hardware | Approx. runtime |
|---|---|---|---|
| `train_legal_bert.ipynb` | Fine-tune `nlpaueb/legal-bert-base-uncased` on CUAD + the project's seed CSV; push to `freak3123/legal-bert-cuad-v1` | T4 x2 GPU | 25–40 min |
| `train_flan_t5.ipynb` | Fine-tune `google/flan-t5-small` on the Plain English Contracts corpus + seed augmentation; push to `freak3123/flan-t5-simplify-v1` | T4 x2 GPU | 12–20 min |

## Workflow

1. **Upload the seed CSV as a Kaggle dataset** named `legal-clauses-seed`
   (one-click — Datasets → New Dataset → drag `apps/ml/data/clauses_seed.csv`).
   This is required for the Legal-BERT notebook to merge in the sparse-class
   examples. FLAN-T5 doesn't need it (pulls its training data from GitHub).
2. **Open the notebook in Kaggle**: Code → New Notebook → File → Import Notebook → upload the `.ipynb`.
3. **Configure the environment** in the right sidebar:
   - Accelerator → **GPU T4 x2** (avoid P100 — the current Kaggle PyTorch
     build drops kernels for sm_6.0 and crashes with
     `cudaErrorNoKernelImageForDevice` on P100)
   - Internet → On
   - Add-ons → Secrets → `HF_TOKEN` (write-scope token from
     https://huggingface.co/settings/tokens)
4. **Run All**. Watch the per-epoch metrics; training stops early if val F1
   stops improving.
5. The last cell pushes the model to the Hub. Note the test-set macro F1 /
   rougeL printed in the evaluation cell — that's the number that goes in
   `docs/evaluation.md`.

## After training finishes

`apps/ml/app/config.py` already pins the two Hub IDs (`freak3123/...`).
The FastAPI service loads them at startup via
`AutoModelForSequenceClassification.from_pretrained()` (classifier) and
`AutoModelForSeq2SeqLM.from_pretrained()` (rewriter), with sklearn and
template fallbacks if either Hub model is unreachable.

To deploy:

1. Push the repo to GitHub.
2. Create a Hugging Face Space (Docker SDK) named `freak3123/legal-rewriter-ml`.
3. `git subtree push --prefix apps/ml hf-space main` to push the ML service.
4. The Space will pull both models on cold start.

See `docs/deploy-guide.md` for the full step-by-step.

## Why notebooks here, training there?

We keep notebooks in version control so the choice of label mapping,
hyperparameters, and eval splits is auditable. But we run them on Kaggle
because:

- Kaggle gives free T4 x2 GPUs; your laptop probably doesn't have one.
- A failed Kaggle session doesn't burn a local checkpoint.
- The training output (HF Hub model) lives somewhere everyone can pull from,
  so deployment doesn't need anyone's laptop.

## Datasets

Don't commit the actual datasets — reference them by Hub IDs / URLs:

| Dataset | Source | Use |
|---|---|---|
| CUAD | downloaded from GitHub raw URL inside the notebook | Clause classification |
| `apps/ml/data/clauses_seed.csv` | committed to the repo (227 rows, hand-curated) | Boosts the 5 sparse classes |
| Plain English Contracts | `lauramanor/legal_summarization` (GitHub raw) | Rewriter training pairs |

## See also

- `docs/architecture.md` — overall system design
- `docs/deploy-guide.md` — Kaggle / GitHub / HF Spaces / Vercel step-by-step
- `docs/api-contract.md` — JSON contract between web and ml
