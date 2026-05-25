"""Generate the Phase 3 figures for the report/paper/presentation:

  1. results_chart.png            — overwrites the stale baseline chart with the
                                    fine-tuned Legal-BERT numbers.
  2. comparison_baseline_bert.png — TF-IDF baseline vs Legal-BERT macro F1.
  3. flan_t5_rouge_curves.png     — ROUGE-{1,2,L} across 10 training epochs.
  4. confusion_matrix.png         — full 12x12 heat-map for Legal-BERT on the
                                    held-out test set. Requires the HF model to
                                    be reachable (downloads ~440 MB the first
                                    time). Skipped with a warning if it's not.

Run from the project root:
    cd materials && python gen_figures_phase3.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

# Theme — match the existing generate_results_chart.py palette
NAVY, BLUE, GREEN, GREYC, DK = "#1A3260", "#4590B8", "#42955F", "#969FA7", "#3D3D3D"
RED = "#C44E52"

# Use a font available on Windows; fall back gracefully.
for font in ["Gill Sans MT", "Calibri", "Arial", "DejaVu Sans"]:
    plt.rcParams["font.family"] = font
    break
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = Path(__file__).resolve().parent.parent / "figures"
OUT_DIR.mkdir(exist_ok=True)

# -----------------------------------------------------------------------------
# Source of truth: held-out test-set numbers from the Kaggle eval cell
# (Legal-BERT, freak3123/legal-bert-cuad-v1, 4-epoch fine-tune on CUAD + seed).
# -----------------------------------------------------------------------------

CLASSES = [
    "GOVERNING_LAW", "INDEMNIFICATION", "LIABILITY", "TERMINATION",
    "INTELLECTUAL_PROPERTY", "WARRANTY", "OTHER",
    "CONFIDENTIALITY", "DEFINITIONS", "DISPUTE_RESOLUTION",
    "PAYMENT", "RENEWAL",
]
PRECISION = [1.000, 0.982, 0.987, 0.946, 0.878, 0.581, 0.914, 1.000, 1.000, 0.600, 0.800, 0.750]
RECALL    = [0.957, 0.964, 0.938, 0.946, 0.889, 1.000, 0.790, 1.000, 1.000, 1.000, 1.000, 1.000]
F1        = [0.978, 0.973, 0.962, 0.946, 0.883, 0.735, 0.848, 1.000, 1.000, 0.750, 0.889, 0.857]
SUPPORT   = [47, 56, 81, 37, 81, 18, 81, 4, 4, 3, 4, 3]
ACCURACY = 0.912
WEIGHTED_F1 = 0.915
MACRO_F1 = 0.902

# Baseline (TF-IDF + LogReg, seed-only training) per-class F1, for the
# comparison figure. Source: the pre-expansion CV report in HANDOVER.md plus the
# updated retrain on the expanded seed CSV.
BASELINE_MACRO_F1 = 0.61   # seed-only with expanded CSV
LEGAL_BERT_MACRO_F1 = MACRO_F1

# FLAN-T5 ROUGE history from the Kaggle epoch log
T5_EPOCHS = list(range(1, 11))
T5_ROUGE1 = [0.2746, 0.2872, 0.3165, 0.3527, 0.3352, 0.3562, 0.3725, 0.3774, 0.3775, 0.3938]
T5_ROUGE2 = [0.0745, 0.1234, 0.1500, 0.1805, 0.1607, 0.1905, 0.2140, 0.2072, 0.2124, 0.2314]
T5_ROUGEL = [0.2244, 0.2535, 0.2699, 0.3078, 0.2908, 0.3159, 0.3276, 0.3324, 0.3341, 0.3523]


# -----------------------------------------------------------------------------
# Figure 1 — updated per-class results
# -----------------------------------------------------------------------------


def figure_results_chart() -> None:
    fig = plt.figure(figsize=(15, 5.9), dpi=170)
    gs = fig.add_gridspec(2, 1, height_ratios=[1.0, 4.8], hspace=0.30)

    ax_top = fig.add_subplot(gs[0])
    ax_top.axis("off")
    ax_top.set_xlim(0, 1)
    ax_top.set_ylim(0, 1)

    def metric_box(x: float, label: str, value: str, colour: str) -> None:
        ax_top.add_patch(
            mpatches.FancyBboxPatch(
                (x, 0.10), 0.20, 0.78,
                boxstyle="round,pad=0.02",
                linewidth=1.2, edgecolor=colour, facecolor="#EEF1F6",
            )
        )
        ax_top.text(x + 0.10, 0.62, value, ha="center", va="center",
                    fontsize=22, fontweight="bold", color=NAVY)
        ax_top.text(x + 0.10, 0.25, label, ha="center", va="center",
                    fontsize=11, color=DK)

    metric_box(0.06, "Overall Accuracy",    f"{ACCURACY:.3f}",    NAVY)
    metric_box(0.30, "Weighted-Average F1", f"{WEIGHTED_F1:.3f}", GREEN)
    metric_box(0.54, "Macro-Average F1",    f"{MACRO_F1:.3f}",    BLUE)
    metric_box(0.78, "Automated Tests",     "34 / 34",            NAVY)

    ax = fig.add_subplot(gs[1])
    x = np.arange(len(CLASSES))
    width = 0.26
    ax.bar(x - width, PRECISION, width, label="Precision",
           color=NAVY, edgecolor=NAVY, linewidth=0.5)
    ax.bar(x, RECALL, width, label="Recall",
           color=BLUE, edgecolor=NAVY, linewidth=0.5)
    ax.bar(x + width, F1, width, label="F1-score",
           color=GREEN, edgecolor=NAVY, linewidth=0.5)

    for xi, v in zip(x, F1):
        ax.text(xi + width, v + 0.02, f"{v:.2f}", ha="center", va="bottom",
                fontsize=8, color=GREEN)

    ax.set_xticks(x)
    ax.set_xticklabels([f"{c}\n(n={s})" for c, s in zip(CLASSES, SUPPORT)],
                       rotation=22, ha="right", fontsize=8.6, color=DK)
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("Score", fontsize=11, color=DK)
    ax.set_title(
        "Per-Class Classifier Performance — Legal-BERT fine-tuned on CUAD + seed (held-out test set)",
        fontsize=13, fontweight="bold", pad=10, color=NAVY,
    )
    ax.axhline(0.80, color=GREYC, linestyle="--", linewidth=1.0)
    ax.text(len(CLASSES) - 0.45, 0.82, "Project target: F1 = 0.80",
            ha="right", va="bottom", fontsize=8.5, color=DK, style="italic")
    ax.yaxis.set_major_locator(plt.MultipleLocator(0.1))
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    ax.set_axisbelow(True)
    for sp in ax.spines.values():
        sp.set_color(GREYC)
    ax.tick_params(colors=GREYC)
    ax.legend(loc="upper right", frameon=True, fontsize=10)

    path = OUT_DIR / "results_chart.png"
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {path.name}")


# -----------------------------------------------------------------------------
# Figure 2 — baseline vs fine-tuned comparison
# -----------------------------------------------------------------------------


def figure_baseline_vs_bert() -> None:
    fig, ax = plt.subplots(figsize=(8, 5.5), dpi=170)
    methods = ["TF-IDF + LogReg\n(baseline)", "Legal-BERT\n(fine-tuned on CUAD + seed)"]
    f1s = [BASELINE_MACRO_F1, LEGAL_BERT_MACRO_F1]
    colours = [GREYC, NAVY]

    bars = ax.bar(methods, f1s, color=colours, edgecolor=NAVY, linewidth=1.2, width=0.55)
    for bar, val in zip(bars, f1s):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.015, f"{val:.3f}",
                ha="center", va="bottom", fontsize=13, fontweight="bold", color=NAVY)

    lift = LEGAL_BERT_MACRO_F1 - BASELINE_MACRO_F1
    ax.annotate(
        f"+{lift:.3f} ({lift / BASELINE_MACRO_F1 * 100:.0f}% relative)",
        xy=(1, LEGAL_BERT_MACRO_F1), xytext=(0.55, 0.78),
        fontsize=11, color=GREEN, fontweight="bold",
        arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.5),
    )

    ax.axhline(0.80, color=GREYC, linestyle="--", linewidth=1.0)
    ax.text(1.45, 0.81, "Project target: macro F1 = 0.80",
            ha="right", va="bottom", fontsize=9, color=DK, style="italic")

    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Macro-Average F1 (held-out test set)", fontsize=11, color=DK)
    ax.set_title("Baseline vs Fine-tuned: classification head-line metric",
                 fontsize=13, fontweight="bold", pad=10, color=NAVY)
    ax.yaxis.set_major_locator(plt.MultipleLocator(0.1))
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    ax.set_axisbelow(True)
    for sp in ax.spines.values():
        sp.set_color(GREYC)
    ax.tick_params(colors=GREYC)

    path = OUT_DIR / "comparison_baseline_bert.png"
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {path.name}")


# -----------------------------------------------------------------------------
# Figure 3 — FLAN-T5 ROUGE curves
# -----------------------------------------------------------------------------


def figure_flan_t5_rouge() -> None:
    fig, ax = plt.subplots(figsize=(9, 5.2), dpi=170)
    ax.plot(T5_EPOCHS, T5_ROUGE1, marker="o", color=NAVY,  linewidth=2,  label="ROUGE-1")
    ax.plot(T5_EPOCHS, T5_ROUGEL, marker="s", color=BLUE,  linewidth=2,  label="ROUGE-L")
    ax.plot(T5_EPOCHS, T5_ROUGE2, marker="^", color=GREEN, linewidth=2,  label="ROUGE-2")

    final_label = (
        f"final: R-1={T5_ROUGE1[-1]:.3f}, R-L={T5_ROUGEL[-1]:.3f}, R-2={T5_ROUGE2[-1]:.3f}"
    )
    ax.text(T5_EPOCHS[-1] - 0.2, T5_ROUGE1[-1] + 0.02, final_label,
            ha="right", va="bottom", fontsize=9, color=DK, style="italic")

    ax.set_xticks(T5_EPOCHS)
    ax.set_xlim(0.6, len(T5_EPOCHS) + 0.4)
    ax.set_ylim(0, 0.55)
    ax.set_xlabel("Training epoch", fontsize=11, color=DK)
    ax.set_ylabel("ROUGE (validation set)", fontsize=11, color=DK)
    ax.set_title("FLAN-T5-small clause simplifier — ROUGE on validation across 10 epochs",
                 fontsize=12, fontweight="bold", pad=10, color=NAVY)
    ax.yaxis.set_major_locator(plt.MultipleLocator(0.1))
    ax.grid(linestyle=":", alpha=0.5)
    ax.set_axisbelow(True)
    for sp in ax.spines.values():
        sp.set_color(GREYC)
    ax.tick_params(colors=GREYC)
    ax.legend(loc="lower right", frameon=True, fontsize=10)

    path = OUT_DIR / "flan_t5_rouge_curves.png"
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {path.name}")


# -----------------------------------------------------------------------------
# Figure 4 — confusion matrix (12x12)
# -----------------------------------------------------------------------------


def figure_confusion_matrix() -> None:
    """Compute the confusion matrix by running the deployed HF model on the
    same held-out CUAD + seed test slice that the Kaggle notebook used.

    Skipped if the HF model is unreachable.
    """
    apps_ml = OUT_DIR.parent / "apps" / "ml"
    if not apps_ml.exists():
        print("skipped confusion_matrix: apps/ml not found")
        return

    sys.path.insert(0, str(apps_ml))
    os.environ.pop("LEGAL_REWRITER_DISABLE_HF", None)

    try:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
    except ImportError:
        print("skipped confusion_matrix: transformers/torch not available locally")
        return

    repo_id = "freak3123/legal-bert-cuad-v1"
    try:
        tok = AutoTokenizer.from_pretrained(repo_id)
        model = AutoModelForSequenceClassification.from_pretrained(repo_id)
    except Exception as exc:
        print(f"skipped confusion_matrix: cannot load {repo_id}: {exc}")
        return
    model.eval()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)

    from sklearn.metrics import confusion_matrix
    from sklearn.model_selection import train_test_split

    from scripts.train_classifier import load_cuad, load_seed, SEED_PATH  # type: ignore

    SEED = 42
    cuad_texts, cuad_labels = load_cuad(max_per_class=800, seed=SEED)
    if SEED_PATH.exists():
        st, sl = load_seed(SEED_PATH)
        cuad_texts.extend(st)
        cuad_labels.extend(sl)

    LABELS = [
        "LIABILITY", "TERMINATION", "PAYMENT", "CONFIDENTIALITY",
        "INDEMNIFICATION", "INTELLECTUAL_PROPERTY", "GOVERNING_LAW",
        "DISPUTE_RESOLUTION", "DEFINITIONS", "RENEWAL", "WARRANTY", "OTHER",
    ]
    label2id = {l: i for i, l in enumerate(LABELS)}
    y = [label2id[l] for l in cuad_labels]
    _, x_test, _, y_test = train_test_split(
        cuad_texts, y, test_size=0.1, random_state=SEED, stratify=y,
    )

    preds: list[int] = []
    batch = 16
    print(f"running HF model on {len(x_test)} test clauses…")
    with torch.no_grad():
        for i in range(0, len(x_test), batch):
            chunk = x_test[i : i + batch]
            enc = tok(chunk, return_tensors="pt", truncation=True,
                      max_length=256, padding=True).to(device)
            logits = model(**enc).logits
            preds.extend(logits.argmax(-1).cpu().tolist())

    cm = confusion_matrix(y_test, preds, labels=list(range(len(LABELS))))

    fig, ax = plt.subplots(figsize=(10, 8.5), dpi=170)
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(np.arange(len(LABELS)))
    ax.set_yticks(np.arange(len(LABELS)))
    ax.set_xticklabels(LABELS, rotation=45, ha="right", fontsize=9, color=DK)
    ax.set_yticklabels(LABELS, fontsize=9, color=DK)
    ax.set_xlabel("Predicted label", fontsize=11, color=DK)
    ax.set_ylabel("True label", fontsize=11, color=DK)
    ax.set_title("Confusion matrix — Legal-BERT on held-out test set",
                 fontsize=13, fontweight="bold", pad=10, color=NAVY)

    # Annotate each cell; light text on dark cells, dark text on light cells.
    threshold = cm.max() / 2.0
    for i in range(len(LABELS)):
        for j in range(len(LABELS)):
            if cm[i, j] == 0:
                continue
            colour = "white" if cm[i, j] > threshold else NAVY
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                    fontsize=9, color=colour)

    cbar = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.04)
    cbar.set_label("Count", color=DK, fontsize=10)

    path = OUT_DIR / "confusion_matrix.png"
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {path.name}")


if __name__ == "__main__":
    figure_results_chart()
    figure_baseline_vs_bert()
    figure_flan_t5_rouge()
    figure_confusion_matrix()
