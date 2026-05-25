"""Clause segmentation — splits a document into individual clauses.

Strategy, in priority order:
  1. Structural markers: "1.", "1)", "(1)", "1.1", "(a)", "(i)", "Section 5", etc.
  2. Blank-line paragraph splitting.
  3. Sentence splitting via spaCy's rule-based sentencizer (no model download
     needed — uses spacy.lang.en blank pipeline + the `sentencizer` component).

Each segment carries its char span back into the original input so downstream
NER can report absolute offsets.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class Segment:
    text: str
    start: int
    end: int


@lru_cache(maxsize=1)
def _sentencizer():
    """Lazy-init a blank English pipeline with the rule-based sentencizer.

    No model download required; this is shipped with spaCy core. Cached so we
    only pay the construction cost once per process.
    """
    from spacy.lang.en import English

    nlp = English()
    nlp.add_pipe("sentencizer")
    return nlp


# Matches a clause start-marker at the beginning of a line.
# Examples it catches:
#   "1." "1.1" "1.1.1" "12)" "(1)" "(a)" "(i)" "Section 5" "Article III"
_CLAUSE_START = re.compile(
    r"""
    ^                      # line start
    (?:
        \(?\d+(?:\.\d+)*[.\)]      # 1.  1.1  (1)  1)  3.2.1.
        |
        \(?[a-zA-Z]\)               # (a)  a)  A)
        |
        \(?[ivxIVX]+\)              # (i) (ii) (IV)
        |
        (?:Section|Article|Clause|§)\s+\S+   # Section 5  Article III
    )
    \s+                    # at least one space after the marker
    """,
    re.MULTILINE | re.VERBOSE,
)


def segment_clauses(text: str, max_clauses: int = 200) -> list[Segment]:
    """Split text into clauses.

    The strategy: find every clause-start marker, treat the text between two
    consecutive markers as one clause. Falls back to paragraph splitting when
    no markers are detected.
    """
    if not text.strip():
        return []

    matches = list(_CLAUSE_START.finditer(text))

    # Fallback: no structural markers found — split on blank lines
    if not matches:
        return _segment_by_paragraph(text, max_clauses=max_clauses)

    segments: list[Segment] = []
    starts = [m.start() for m in matches] + [len(text)]
    for i in range(len(starts) - 1):
        chunk = text[starts[i] : starts[i + 1]].strip()
        if not chunk:
            continue
        # Compute the start offset of the trimmed chunk
        leading = len(text[starts[i] : starts[i + 1]]) - len(
            text[starts[i] : starts[i + 1]].lstrip()
        )
        s = starts[i] + leading
        e = s + len(chunk)
        segments.append(Segment(text=chunk, start=s, end=e))
        if len(segments) >= max_clauses:
            break

    # Sanity: if structural markers gave us a single huge chunk (e.g. one
    # numbered "1." followed by 20 paragraphs), still try paragraph fallback
    # for anything > 2000 chars.
    expanded: list[Segment] = []
    for seg in segments:
        if len(seg.text) > 2000:
            expanded.extend(_split_long_segment(seg))
        else:
            expanded.append(seg)

    return expanded[:max_clauses]


def _segment_by_paragraph(text: str, max_clauses: int) -> list[Segment]:
    """Fallback: split on blank lines, then further split multi-sentence paragraphs."""
    segments: list[Segment] = []
    cursor = 0
    for para in re.split(r"\n\s*\n", text):
        stripped = para.strip()
        if not stripped:
            cursor += len(para) + 2
            continue
        idx = text.find(stripped, cursor)
        if idx == -1:
            idx = cursor
        # If the paragraph is itself multi-sentence, split it further so each
        # sentence becomes its own clause. Single-sentence paragraphs pass through.
        for sent in _split_sentences(stripped, base_offset=idx):
            segments.append(sent)
            if len(segments) >= max_clauses:
                return segments
        cursor = idx + len(stripped)
    return segments


def _split_sentences(paragraph: str, base_offset: int) -> list[Segment]:
    """Run the sentencizer on a paragraph and return sentence-level segments.

    Falls back to a single segment for the whole paragraph if the sentencizer
    finds only one sentence (the common case for short numbered items).
    """
    nlp = _sentencizer()
    doc = nlp(paragraph)
    sents = [s for s in doc.sents if s.text.strip()]
    if len(sents) <= 1:
        return [Segment(text=paragraph, start=base_offset, end=base_offset + len(paragraph))]
    out: list[Segment] = []
    for sent in sents:
        # spaCy's start_char/end_char are offsets within `paragraph`; shift to absolute.
        s = base_offset + sent.start_char
        e = base_offset + sent.end_char
        out.append(Segment(text=sent.text.strip(), start=s, end=e))
    return out


def _split_long_segment(seg: Segment) -> list[Segment]:
    """Break overly long segments at paragraph boundaries while preserving offsets."""
    out: list[Segment] = []
    parts = re.split(r"(\n\s*\n)", seg.text)
    cursor = seg.start
    buffer = ""
    buffer_start = cursor
    for part in parts:
        if part.strip() == "":
            cursor += len(part)
            continue
        if not buffer:
            buffer_start = cursor
        if len(buffer) + len(part) > 1500 and buffer:
            out.append(
                Segment(
                    text=buffer.strip(),
                    start=buffer_start,
                    end=buffer_start + len(buffer),
                )
            )
            buffer = part
            buffer_start = cursor
        else:
            buffer += part
        cursor += len(part)
    if buffer.strip():
        out.append(
            Segment(
                text=buffer.strip(),
                start=buffer_start,
                end=buffer_start + len(buffer),
            )
        )
    return out or [seg]
