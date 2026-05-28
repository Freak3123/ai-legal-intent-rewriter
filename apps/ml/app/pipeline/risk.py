"""Risk flagging: three-layer rule-based system.

This is the ONE pipeline component that doesn't need ML — the planning doc
calls for transparent, deterministic rules. So this is implemented for real,
not stubbed. Tune thresholds and triggers in `app/config.py`.

Layers:
  1. Keyword matching   — curated dictionary of red-flag phrases
  2. Regex patterns     — structural risk indicators (short notice, etc.)
  3. Heuristic scoring  — combines layers into low/medium/high
"""

from __future__ import annotations

import contextlib
import re

from app.config import settings
from app.pipeline.classify import NOTICE_DAYS_RE
from app.schemas import ClassificationLabel, Risk, RiskLevel

# -----------------------------------------------------------------------------
# Layer 1: Keyword dictionary
# Each entry: trigger-name → (regex pattern, score weight 0–1)
# -----------------------------------------------------------------------------

_KEYWORD_TRIGGERS: dict[str, tuple[re.Pattern[str], float]] = {
    "irrevocable": (re.compile(r"\birrevocab(?:le|ly)\b", re.I), 0.4),
    "sole-discretion": (re.compile(r"\bsole\s+discretion\b", re.I), 0.5),
    "automatic-renewal": (re.compile(r"\bautomatic(?:ally)?\s+renew", re.I), 0.4),
    "waive-rights": (re.compile(r"\bwaiv(?:e|er)\s+(?:any|all)\s+right", re.I), 0.6),
    "liquidated-damages": (re.compile(r"\bliquidated\s+damages\b", re.I), 0.4),
    "non-refundable": (re.compile(r"\bnon-?refundable\b", re.I), 0.3),
    "indemnify-and-hold-harmless": (
        re.compile(r"\bindemnify\s+(?:,?\s*defend\s*,?\s*)?and\s+hold\s+harmless\b", re.I),
        0.5,
    ),
    "time-of-the-essence": (re.compile(r"\btime\s+is\s+of\s+the\s+essence\b", re.I), 0.3),
    "uncapped-liability": (
        re.compile(r"\b(?:unlimited|uncapped)\s+liability\b", re.I),
        0.7,
    ),
    "no-warranty": (
        re.compile(r"\b(?:as[- ]is|without\s+(?:any\s+)?warrant(?:ies|y))\b", re.I),
        0.4,
    ),
    "binding-arbitration": (re.compile(r"\bbinding\s+arbitration\b", re.I), 0.3),
    "class-action-waiver": (
        re.compile(r"\b(?:waiv\w+\s+(?:any\s+right\s+to\s+)?(?:a\s+)?class\s+action|"
                   r"class\s+action\s+waiver)\b", re.I),
        0.6,
    ),
    "unilateral-amendment": (
        re.compile(r"\b(?:may|reserves?\s+the\s+right\s+to)\s+(?:modify|amend|change)\s+"
                   r"(?:these|this|the)\s+(?:terms|agreement)\s+(?:at\s+any\s+time|"
                   r"in\s+(?:its|their)\s+(?:sole\s+)?discretion)", re.I),
        0.6,
    ),
}


# -----------------------------------------------------------------------------
# Layer 2: Regex / structural patterns
# -----------------------------------------------------------------------------

_NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "twenty": 20, "thirty": 30,
    "sixty": 60, "ninety": 90,
}


def _extract_notice_days(text: str) -> int | None:
    """Find the smallest 'X days' duration mentioned. None if no day mentions."""
    days: list[int] = []
    for m in NOTICE_DAYS_RE.finditer(text):
        digit_group = m.group(1)
        if digit_group:
            with contextlib.suppress(ValueError):
                days.append(int(digit_group))
            continue
        # Check for "thirty (30)" style — already caught by digit_group above
        # but also handle bare word numbers
        word = m.group(0).lower()
        for w, n in _NUMBER_WORDS.items():
            if w in word:
                days.append(n)
                break
    return min(days) if days else None


def _detect_short_notice(text: str, label: ClassificationLabel) -> tuple[bool, float]:
    """Termination / cancellation clauses with notice <= threshold are risky."""
    if label not in {"TERMINATION", "RENEWAL", "PAYMENT"}:
        return False, 0.0
    days = _extract_notice_days(text)
    if days is None:
        return False, 0.0
    if days <= settings.short_notice_days_threshold:
        return True, 0.5
    return False, 0.0


def _detect_one_sided_termination(text: str) -> tuple[bool, float]:
    """'Company may terminate at any time without cause' — one-sided termination."""
    pattern = re.compile(
        r"(?:company|licensor|service\s+provider|landlord|employer)\s+"
        r"(?:may|reserves?\s+the\s+right\s+to)\s+terminate"
        r"(?:[^.]{0,80}(?:at\s+any\s+time|without\s+(?:cause|notice|reason)))",
        re.I,
    )
    return (bool(pattern.search(text)), 0.5)


# -----------------------------------------------------------------------------
# Layer 3: Combine into a final score
# -----------------------------------------------------------------------------


def _score_to_level(score: float) -> RiskLevel:
    if score >= settings.high_risk_score_threshold:
        return "high"
    if score >= settings.medium_risk_score_threshold:
        return "medium"
    return "low"


def assess_risk(text: str, label: ClassificationLabel) -> Risk:
    """Run all three layers and return a final Risk verdict."""
    triggers: list[str] = []
    score = 0.0

    # Layer 1: keyword triggers
    for name, (pattern, weight) in _KEYWORD_TRIGGERS.items():
        if pattern.search(text):
            triggers.append(name)
            score += weight

    # Layer 2: structural patterns
    short_notice, weight = _detect_short_notice(text, label)
    if short_notice:
        triggers.append("short-notice-period")
        score += weight

    one_sided, weight = _detect_one_sided_termination(text)
    if one_sided:
        triggers.append("unilateral-termination")
        score += weight

    # Layer 3: cap and normalise
    score = min(1.0, score)
    level = _score_to_level(score)

    return Risk(
        level=level,
        score=round(score, 3),
        triggers=triggers,
    )
