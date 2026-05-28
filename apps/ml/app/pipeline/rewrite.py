"""Intent rewriting: legal clause → plain English.

Two-layer resolver:

1. Fine-tuned FLAN-T5-small loaded via the HF Hub pin in
   ``app.config.model_versions.rewriter``. method='model' in responses.
2. Template + rule-based simplification fallback. method='template-fallback'.

Loads lazily on first call; ``warm_up()`` triggers the load at app startup.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from app.config import model_versions
from app.schemas import ClassificationLabel, Rewrite

logger = logging.getLogger(__name__)

_PREFIX = "simplify legal: "
_MAX_INPUT = 384
_MAX_TARGET = 192

# Module-level cache. None = not loaded yet; (None, None) = tried and failed.
_hf_state: tuple[Any, Any] | None = None

_LABEL_OPENERS: dict[ClassificationLabel, str] = {
    "TERMINATION": "This clause covers when and how the contract can be ended.",
    "RENEWAL": "This clause sets out how the contract gets renewed.",
    "LIABILITY": "This clause limits what either side can claim if something goes wrong.",
    "INDEMNIFICATION": (
        "This clause says one side has to cover the other's losses in certain situations."
    ),
    "CONFIDENTIALITY": "This clause says some information has to be kept private.",
    "PAYMENT": "This clause sets out how and when money has to be paid.",
    "INTELLECTUAL_PROPERTY": "This clause decides who owns the creative or technical work.",
    "GOVERNING_LAW": "This clause picks which country's laws apply to the contract.",
    "DISPUTE_RESOLUTION": "This clause sets out how arguments about the contract get resolved.",
    "DEFINITIONS": "This clause explains what specific terms mean throughout the contract.",
    "WARRANTY": "This clause spells out what is or isn't guaranteed about the product or service.",
    "OTHER": "Here's a plain-English version of this clause.",
}


def _is_hf_pin(pin: str) -> bool:
    return "/" in pin and not pin.startswith(".")


def _load_hf_model() -> tuple[Any, Any] | tuple[None, None]:
    """Load the fine-tuned FLAN-T5 from the Hub. Caches the result."""
    import os

    global _hf_state
    if _hf_state is not None:
        return _hf_state

    if os.environ.get("LEGAL_REWRITER_DISABLE_HF") == "1":
        _hf_state = (None, None)
        return _hf_state

    pin = model_versions.rewriter
    if not _is_hf_pin(pin):
        _hf_state = (None, None)
        return _hf_state

    try:
        import torch
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        logger.info("loading HF rewriter %s", pin)
        tokenizer = AutoTokenizer.from_pretrained(pin)
        model = AutoModelForSeq2SeqLM.from_pretrained(pin)
        model.eval()
        if torch.cuda.is_available():
            model = model.to("cuda")
        _hf_state = (model, tokenizer)
        logger.info("HF rewriter loaded")
    except Exception as exc:
        logger.warning("failed to load HF rewriter %s: %s", pin, exc)
        _hf_state = (None, None)
    return _hf_state


def warm_up() -> None:
    """Trigger model load at app startup."""
    _load_hf_model()


def rewrite_clause(text: str, label: ClassificationLabel) -> Rewrite:
    """Produce a plain-English rewrite of the clause."""
    model, tokenizer = _load_hf_model()
    if model is not None:
        try:
            rewritten = _rewrite_with_model(model, tokenizer, text)
            return Rewrite(
                text=rewritten,
                readability_score=_flesch_kincaid_grade(rewritten),
                method="model",
            )
        except Exception as exc:
            logger.warning("model rewrite failed (%s) — falling back to template", exc)

    opener = _LABEL_OPENERS.get(label, _LABEL_OPENERS["OTHER"])
    simplified = _simplify(text)
    rewrite_text = (
        f"{opener} See the original text for the full details."
        if len(simplified) > 300
        else f"{opener} {simplified}"
    )
    return Rewrite(
        text=rewrite_text,
        readability_score=_flesch_kincaid_grade(rewrite_text),
        method="template-fallback",
    )


def _rewrite_with_model(model: Any, tokenizer: Any, text: str) -> str:
    import torch

    device = next(model.parameters()).device
    inputs = tokenizer(
        _PREFIX + text,
        return_tensors="pt",
        truncation=True,
        max_length=_MAX_INPUT,
    ).to(device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=_MAX_TARGET,
            num_beams=4,
            no_repeat_ngram_size=3,
            early_stopping=True,
        )
    return tokenizer.decode(outputs[0], skip_special_tokens=True).strip()


# -----------------------------------------------------------------------------
# Template-fallback helpers
# -----------------------------------------------------------------------------

_REPLACEMENTS = [
    (r"\bnotwithstanding the foregoing\b", "even so"),
    (r"\bnotwithstanding\b", "even though"),
    (r"\bin no event shall\b", "neither side can"),
    (r"\bshall not\b", "cannot"),
    (r"\bshall\b", "must"),
    (r"\bhereinafter\b", "from now on"),
    (r"\bherein\b", "in this contract"),
    (r"\bhereby\b", ""),
    (r"\bthereof\b", "of it"),
    (r"\bpursuant to\b", "under"),
    (r"\bsubject to\b", "as long as"),
    (r"\bin accordance with\b", "following"),
    (r"\bprovided, however, that\b", "but only if"),
    (r"\bprovided that\b", "as long as"),
    (r"\bincluding, without limitation,\b", "including"),
    (r"\bincluding without limitation\b", "including"),
    (r"\bwithout limitation\b", ""),
    (r"\bany and all\b", "all"),
    (r"\bnull and void\b", "void"),
    (r"\bdue and payable\b", "due"),
    (r"\bcease and desist\b", "stop"),
    (r"\bunless and until\b", "until"),
    (r"\bat its sole discretion\b", "at their own choice"),
    (r"\bin its sole discretion\b", "at their own choice"),
    (r"\bfor the avoidance of doubt\b", "just to be clear"),
]


def _simplify(text: str) -> str:
    out = text
    for pattern, replacement in _REPLACEMENTS:
        out = re.sub(pattern, replacement, out, flags=re.IGNORECASE)
    out = re.sub(r"\s+", " ", out).strip()
    sentences = re.split(r"(?<=[.!?])\s+", out)
    return " ".join(sentences[:2]).strip()


def _flesch_kincaid_grade(text: str) -> float:
    words = re.findall(r"\b\w+\b", text)
    sentences = max(1, len(re.findall(r"[.!?]+", text)))
    if not words:
        return 0.0
    syllables = sum(_count_syllables(w) for w in words)
    return round(
        0.39 * (len(words) / sentences) + 11.8 * (syllables / len(words)) - 15.59,
        1,
    )


def _count_syllables(word: str) -> int:
    word = word.lower()
    vowels = "aeiouy"
    count = 0
    prev_was_vowel = False
    for ch in word:
        is_vowel = ch in vowels
        if is_vowel and not prev_was_vowel:
            count += 1
        prev_was_vowel = is_vowel
    if word.endswith("e") and count > 1:
        count -= 1
    return max(1, count)
