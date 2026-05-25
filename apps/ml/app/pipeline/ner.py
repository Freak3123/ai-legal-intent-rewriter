"""Named entity recognition.

Two-layer hybrid:

1. Regex extractors (the Phase 2 baseline) — restrictive, high precision.
   Cover all six entity types: DATE, AMOUNT, PARTY, RIGHT, OBLIGATION,
   CONDITION.
2. spaCy ``en_core_web_sm`` enrichment — adds recall for DATE / AMOUNT /
   PARTY by mapping native spaCy labels (DATE, MONEY, PERCENT, ORG, PERSON,
   GPE) into our taxonomy. Skipped silently if the model isn't available.

Regex spans take precedence on overlap so model errors can't override the
hand-tuned patterns.
"""

from __future__ import annotations

import logging
import re
from functools import lru_cache
from typing import Any

from app.schemas import Entity

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Regex layer
# -----------------------------------------------------------------------------

_DATE_PATTERNS = [
    re.compile(
        r"\b(?:\d{1,2}\s+(?:January|February|March|April|May|June|July|"
        r"August|September|October|November|December)\s+\d{4})\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"),
    re.compile(
        r"\b(?:thirty\s*\(30\)|sixty\s*\(60\)|ninety\s*\(90\)|"
        r"fifteen\s*\(15\)|seven\s*\(7\)|ten\s*\(10\)|"
        r"\d+)\s*(?:calendar\s+)?(?:days?|months?|years?|weeks?)\b",
        re.IGNORECASE,
    ),
]

_AMOUNT_PATTERNS = [
    re.compile(r"(?:USD|US\$|\$|GBP|£|EUR|€|INR|Rs\.?|₹)\s?\d[\d,]*(?:\.\d+)?", re.IGNORECASE),
    re.compile(r"\b\d+(?:\.\d+)?\s*(?:percent|%)\b", re.IGNORECASE),
    re.compile(
        r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|"
        r"twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million)"
        r"(?:[-\s](?:and\s)?[a-z]+)*\s*\(\d+(?:\.\d+)?\)\s*(?:dollars|rupees|pounds|euros)\b",
        re.IGNORECASE,
    ),
]

_PARTY_PATTERN = re.compile(
    r"\bthe\s+("
    r"Customer|Client|Company|Tenant|Landlord|Licensor|Licensee|"
    r"Vendor|Supplier|Buyer|Seller|Service\s+Provider|"
    r"Employer|Employee|Contractor|Consultant|Party|Parties"
    r")\b"
)

_RIGHT_PATTERNS = [
    re.compile(
        r"\b(?:the\s+)?right\s+to\s+[a-z]+(?:\s+[a-z]+){0,3}\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bmay\s+(?:terminate|assign|sublicen[cs]e|disclose|access|use|"
        r"audit|inspect|modify|withhold|offset|reject|suspend|cancel)\b",
        re.IGNORECASE,
    ),
]

_OBLIGATION_PATTERNS = [
    re.compile(
        r"\bshall\s+(?:pay|deliver|maintain|comply|notify|provide|ensure|"
        r"defend|indemnify|warrant|return|destroy|preserve|cooperate|"
        r"reimburse|disclose|protect|hold|use|treat)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bmust\s+[a-z]+\b", re.IGNORECASE),
    re.compile(r"\b(?:is|are)\s+required\s+to\s+[a-z]+\b", re.IGNORECASE),
    re.compile(r"\b(?:is|are)\s+obligated\s+to\s+[a-z]+\b", re.IGNORECASE),
]

_CONDITION_PATTERNS = [
    re.compile(
        r"\bin\s+the\s+event\s+(?:of|that)\s+[a-z][^,.;]{0,60}",
        re.IGNORECASE,
    ),
    re.compile(r"\bsubject\s+to\s+[a-z][^,.;]{0,60}", re.IGNORECASE),
    re.compile(r"\bprovided\s+that\s+[a-z][^,.;]{0,80}", re.IGNORECASE),
    re.compile(r"\bunless\s+(?:otherwise\s+)?[a-z][^,.;]{0,40}", re.IGNORECASE),
    re.compile(r"\bif\s+and\s+only\s+if\s+[a-z][^,.;]{0,60}", re.IGNORECASE),
    re.compile(r"\bnotwithstanding\s+[a-z][^,.;]{0,40}", re.IGNORECASE),
]


def _find_all(patterns: list[re.Pattern[str]], text: str, label: str) -> list[Entity]:
    out: list[Entity] = []
    seen: set[tuple[int, int]] = set()
    for pat in patterns:
        for m in pat.finditer(text):
            span = (m.start(), m.end())
            if span in seen:
                continue
            seen.add(span)
            out.append(
                Entity(
                    text=m.group(0),
                    type=label,  # type: ignore[arg-type]
                    start=m.start(),
                    end=m.end(),
                )
            )
    return out


def _regex_entities(text: str) -> list[Entity]:
    entities: list[Entity] = []
    entities.extend(_find_all(_DATE_PATTERNS, text, "DATE"))
    entities.extend(_find_all(_AMOUNT_PATTERNS, text, "AMOUNT"))
    entities.extend(_find_all(_RIGHT_PATTERNS, text, "RIGHT"))
    entities.extend(_find_all(_OBLIGATION_PATTERNS, text, "OBLIGATION"))
    entities.extend(_find_all(_CONDITION_PATTERNS, text, "CONDITION"))

    seen_party_spans: set[tuple[int, int]] = set()
    for m in _PARTY_PATTERN.finditer(text):
        span = (m.start(1), m.end(1))
        if span in seen_party_spans:
            continue
        seen_party_spans.add(span)
        entities.append(
            Entity(text=m.group(1), type="PARTY", start=m.start(1), end=m.end(1))
        )
    return entities


# -----------------------------------------------------------------------------
# spaCy layer
# -----------------------------------------------------------------------------

# spaCy native label → our taxonomy. CARDINAL/ORDINAL etc. are deliberately
# excluded — they cause too many false positives in legal prose.
_SPACY_LABEL_MAP = {
    "DATE": "DATE",
    "TIME": "DATE",
    "MONEY": "AMOUNT",
    "PERCENT": "AMOUNT",
    "QUANTITY": "AMOUNT",
    "ORG": "PARTY",
    "PERSON": "PARTY",
    "GPE": "PARTY",
    "NORP": "PARTY",
}


@lru_cache(maxsize=1)
def _load_spacy() -> Any | None:
    """Load en_core_web_sm. Tries to download if missing. Returns None on failure."""
    import os

    if os.environ.get("LEGAL_REWRITER_DISABLE_SPACY") == "1":
        return None
    try:
        import spacy
    except ImportError:
        return None
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        try:
            from spacy.cli import download

            logger.info("downloading en_core_web_sm (one-time)…")
            download("en_core_web_sm")
            return spacy.load("en_core_web_sm")
        except BaseException as exc:  # SystemExit from spacy.cli + everything else
            logger.warning("spaCy model unavailable (%s) — using regex only", exc)
            return None


def warm_up() -> None:
    """Trigger spaCy load at app startup."""
    _load_spacy()


def _spacy_entities(text: str) -> list[Entity]:
    nlp = _load_spacy()
    if nlp is None:
        return []
    try:
        doc = nlp(text)
    except Exception as exc:  # pragma: no cover — defensive
        logger.warning("spaCy NER failed: %s", exc)
        return []
    out: list[Entity] = []
    for ent in doc.ents:
        mapped = _SPACY_LABEL_MAP.get(ent.label_)
        if mapped is None:
            continue
        out.append(
            Entity(
                text=ent.text,
                type=mapped,  # type: ignore[arg-type]
                start=ent.start_char,
                end=ent.end_char,
            )
        )
    return out


# -----------------------------------------------------------------------------
# Merge regex + spaCy
# -----------------------------------------------------------------------------


def _overlaps(a: Entity, b: Entity) -> bool:
    return not (a.end <= b.start or b.end <= a.start)


def extract_entities(text: str) -> list[Entity]:
    """Extract entities. Regex first (high precision), spaCy adds non-overlapping picks."""
    regex_hits = _regex_entities(text)
    spacy_hits = _spacy_entities(text)

    merged: list[Entity] = list(regex_hits)
    for ent in spacy_hits:
        if any(_overlaps(ent, r) for r in regex_hits):
            continue
        merged.append(ent)

    merged.sort(key=lambda e: e.start)
    return merged
