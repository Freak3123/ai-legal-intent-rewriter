"""Compute held-out precision/recall/F1 for the current classifier.

Builds the same train/val/test split that the Kaggle notebook uses
(``random_state=42``, ``test_size=0.1`` with stratification), runs the test
slice through ``app.pipeline.classify.classify_clause``, and writes a per-class
results table to ``docs/evaluation.md``.

Usage:
    cd apps/ml
    uv run python -m scripts.eval_classifier
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

from app.config import model_versions
from app.pipeline.classify import classify_clause
from scripts.train_classifier import REPO_ROOT, SEED_PATH, load_cuad, load_seed

DOCS_PATH = Path(__file__).resolve().parents[3] / "docs" / "evaluation.md"


def _build_test_set(seed: int = 42) -> tuple[list[str], list[str]]:
    cuad_texts, cuad_labels = load_cuad(max_per_class=800, seed=seed)
    if SEED_PATH.exists():
        seed_texts, seed_labels = load_seed(SEED_PATH)
        cuad_texts.extend(seed_texts)
        cuad_labels.extend(seed_labels)

    # Match the Kaggle notebook split exactly so deployed-model eval numbers
    # are directly comparable.
    x_trainval, x_test, y_trainval, y_test = train_test_split(
        cuad_texts, cuad_labels, test_size=0.1, random_state=seed, stratify=cuad_labels,
    )
    return x_test, y_test


def main() -> int:
    print("Building held-out test split…")
    x_test, y_test = _build_test_set()
    print(f"  test size: {len(x_test)} clauses")
    print(f"  classifier pin: {model_versions.classifier}")

    preds = []
    for i, text in enumerate(x_test):
        if i % 50 == 0:
            print(f"  classified {i}/{len(x_test)}")
        preds.append(classify_clause(text).label)

    report = classification_report(y_test, preds, digits=3, zero_division=0)
    macro = classification_report(y_test, preds, output_dict=True, zero_division=0)[
        "macro avg"
    ]
    overall_acc = sum(1 for p, t in zip(preds, y_test, strict=True) if p == t) / len(y_test)

    print("\n" + report)

    # Write markdown table for the report deliverable
    DOCS_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# Evaluation\n")
    lines.append(f"Held-out test set: **{len(x_test)} clauses** from the CUAD + seed merge ")
    lines.append("(stratified split, seed 42 — same split as the Kaggle training notebook).\n")
    lines.append(f"\n**Classifier:** `{model_versions.classifier}`\n")
    lines.append(f"\n**Accuracy:** {overall_acc:.3f} · **Macro precision:** {macro['precision']:.3f} · ")
    lines.append(f"**Macro recall:** {macro['recall']:.3f} · **Macro F1:** {macro['f1-score']:.3f}\n")
    lines.append("\n## Per-class\n\n")
    lines.append("| Class | Precision | Recall | F1 | Support |\n")
    lines.append("|---|---:|---:|---:|---:|\n")

    label_counts = Counter(y_test)
    report_dict = classification_report(y_test, preds, output_dict=True, zero_division=0)
    for label in sorted(label_counts):
        row = report_dict[label]
        lines.append(
            f"| {label} | {row['precision']:.3f} | {row['recall']:.3f} | "
            f"{row['f1-score']:.3f} | {int(row['support'])} |\n"
        )

    lines.append("\n## Confusion matrix (top mis-predictions)\n\n")
    labels_sorted = sorted(label_counts)
    cm = confusion_matrix(y_test, preds, labels=labels_sorted)
    lines.append("Rows = true label, columns = predicted label.\n\n")
    lines.append("|  | " + " | ".join(labels_sorted) + " |\n")
    lines.append("|---" * (len(labels_sorted) + 1) + "|\n")
    for i, true_label in enumerate(labels_sorted):
        cells = " | ".join(str(int(c)) for c in cm[i])
        lines.append(f"| **{true_label}** | {cells} |\n")

    DOCS_PATH.write_text("".join(lines), encoding="utf-8")
    print(f"\nwrote {DOCS_PATH.relative_to(REPO_ROOT.parent)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
