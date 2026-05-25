# -*- coding: utf-8 -*-
"""Plot Legal-BERT training-loss / validation-loss / validation-macro-F1 across
the 4 epochs of the Kaggle T4 training run."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

NAVY, BLUE, GREEN, GREYC, DK = "#1A3260", "#4590B8", "#42955F", "#969FA7", "#3D3D3D"

EPOCH        = [1, 2, 3, 4]
TRAIN_LOSS   = [2.140, 0.869, 0.481, 0.351]
VAL_LOSS     = [1.592, 0.620, 0.409, 0.370]
MACRO_F1     = [0.512, 0.875, 0.885, 0.877]
ACCURACY     = [0.699, 0.871, 0.883, 0.885]

fig, ax1 = plt.subplots(figsize=(9, 5.4), dpi=170)

ax1.plot(EPOCH, TRAIN_LOSS, marker="o", color=NAVY,  linewidth=2.0, label="Training loss")
ax1.plot(EPOCH, VAL_LOSS,   marker="s", color=BLUE,  linewidth=2.0, label="Validation loss")
ax1.set_xlabel("Training epoch", fontsize=11, color=DK)
ax1.set_ylabel("Cross-entropy loss", fontsize=11, color=DK)
ax1.set_xticks(EPOCH)
ax1.set_ylim(0, max(TRAIN_LOSS) * 1.10)
ax1.grid(linestyle=":", alpha=0.5)
ax1.set_axisbelow(True)
for sp in ax1.spines.values():
    sp.set_color(GREYC)

ax2 = ax1.twinx()
ax2.plot(EPOCH, MACRO_F1, marker="^", color=GREEN, linewidth=2.2, label="Validation macro F1")
ax2.plot(EPOCH, ACCURACY, marker="d", color=GREYC, linewidth=1.6, linestyle="--", label="Validation accuracy")
ax2.set_ylabel("Macro F1 / Accuracy", fontsize=11, color=DK)
ax2.set_ylim(0.4, 1.0)
for sp in ax2.spines.values():
    sp.set_color(GREYC)

# Annotate the best epoch
best_idx = MACRO_F1.index(max(MACRO_F1))
best_ep = EPOCH[best_idx]
best_f1 = MACRO_F1[best_idx]
ax2.annotate(
    f"best checkpoint: epoch {best_ep}\nmacro F1 = {best_f1:.3f}",
    xy=(best_ep, best_f1), xytext=(best_ep - 1.3, best_f1 - 0.18),
    fontsize=10, color=GREEN, fontweight="bold",
    arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.4),
)
ax2.axvline(best_ep, color=GREEN, linestyle=":", alpha=0.4)

# Combined legend
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2,
           loc="center right", frameon=True, fontsize=9.5)

ax1.set_title(
    "Legal-BERT fine-tuning — losses and validation macro F1 across 4 epochs (T4 GPU)",
    fontsize=12, fontweight="bold", pad=10, color=NAVY,
)

from pathlib import Path
out = Path(__file__).resolve().parent.parent / "figures" / "legal_bert_training_curves.png"
out.parent.mkdir(exist_ok=True)
fig.savefig(str(out), bbox_inches="tight", facecolor="white")
print(f"wrote {out.relative_to(out.parent.parent)}")
