# -*- coding: utf-8 -*-
"""Render a side-by-side "legal -> plain English" figure using three representative
clauses run through the fine-tuned FLAN-T5 rewriter on the Hub
(freak3123/flan-t5-simplify-v1).

Run from apps/ml's uv environment so transformers/torch are available, e.g.:
    cd apps/ml && uv run --with matplotlib python ../../materials/gen_rewrite_pairs.py
"""
from __future__ import annotations

import os
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

# Disable HF disable-flag so the fine-tuned model can load
os.environ.pop("LEGAL_REWRITER_DISABLE_HF", None)

CLAUSES = [
    (
        "AUTO RENEWAL",
        "This Agreement shall automatically renew for successive one-year periods "
        "unless you provide written notice of cancellation at least thirty (30) "
        "days before the end of the then-current term.",
    ),
    (
        "USER CONTENT LICENCE",
        "You grant the Company a worldwide, royalty-free, perpetual, irrevocable, "
        "non-exclusive licence to use, copy, modify, distribute and display the "
        "content you submit to the Service.",
    ),
    (
        "DATA SHARING",
        "We may share your personal information with our affiliates, service "
        "providers and business partners for purposes of providing and improving "
        "the Services.",
    ),
]


NAVY = "#1A3260"
BLUE = "#4590B8"
GREEN = "#42955F"
GREYC = "#969FA7"
DK = "#3D3D3D"


def rewrite(text: str, model, tokenizer) -> str:
    import torch

    device = next(model.parameters()).device
    enc = tokenizer(
        "simplify legal: " + text,
        return_tensors="pt", max_length=384, truncation=True,
    ).to(device)
    with torch.no_grad():
        out = model.generate(
            **enc,
            max_length=192,
            num_beams=4,
            no_repeat_ngram_size=3,
            early_stopping=True,
        )
    return tokenizer.decode(out[0], skip_special_tokens=True).strip()


def main() -> None:
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    repo_id = "freak3123/flan-t5-simplify-v1"
    print(f"loading {repo_id}…")
    tok = AutoTokenizer.from_pretrained(repo_id)
    model = AutoModelForSeq2SeqLM.from_pretrained(repo_id)
    model.eval()

    pairs: list[tuple[str, str, str]] = []
    for label, source in CLAUSES:
        plain = rewrite(source, model, tok)
        print(f"--- {label} ---\nLEGAL:  {source}\nPLAIN:  {plain}\n")
        pairs.append((label, source, plain))

    # ----- figure ------------------------------------------------------------
    fig, axes = plt.subplots(
        len(pairs), 1, figsize=(13, 2.4 * len(pairs)), dpi=170,
        gridspec_kw={"hspace": 0.6},
    )

    for ax, (label, legal, plain) in zip(axes, pairs):
        ax.axis("off")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

        # Label badge
        ax.add_patch(mpatches.FancyBboxPatch(
            (0.005, 0.78), 0.16, 0.18,
            boxstyle="round,pad=0.015", facecolor=NAVY, edgecolor=NAVY,
        ))
        ax.text(0.085, 0.87, label, ha="center", va="center",
                fontsize=10, fontweight="bold", color="white")

        # Legal pane
        ax.add_patch(mpatches.FancyBboxPatch(
            (0.18, 0.10), 0.39, 0.85,
            boxstyle="round,pad=0.015", facecolor="#F4F6FA",
            edgecolor=GREYC, linewidth=1,
        ))
        ax.text(0.195, 0.86, "Original (legal)", fontsize=10,
                fontweight="bold", color=NAVY, va="top")
        wrapped_legal = "\n".join(textwrap.wrap(legal, width=58))
        ax.text(0.195, 0.78, wrapped_legal, fontsize=9.5,
                color=DK, va="top", family="serif")

        # Plain pane
        ax.add_patch(mpatches.FancyBboxPatch(
            (0.59, 0.10), 0.40, 0.85,
            boxstyle="round,pad=0.015", facecolor="#EEF7F0",
            edgecolor=GREEN, linewidth=1,
        ))
        ax.text(0.605, 0.86, "FLAN-T5 plain-English rewrite", fontsize=10,
                fontweight="bold", color=GREEN, va="top")
        wrapped_plain = "\n".join(textwrap.wrap(plain, width=58))
        ax.text(0.605, 0.78, wrapped_plain, fontsize=9.5,
                color=DK, va="top", family="serif")

    fig.suptitle(
        "Sample clause rewrites — fine-tuned FLAN-T5-small "
        "(freak3123/flan-t5-simplify-v1)",
        fontsize=13, fontweight="bold", color=NAVY, y=0.995,
    )

    out_path = Path(__file__).resolve().parent.parent / "figures" / "rewrite_examples.png"
    out_path.parent.mkdir(exist_ok=True)
    fig.savefig(str(out_path), bbox_inches="tight", facecolor="white")
    print(f"wrote {out_path.relative_to(out_path.parent.parent)}")


if __name__ == "__main__":
    main()
