"""Tests for the rule + sentencizer clause segmenter."""

from __future__ import annotations

from app.pipeline.segment import Segment, segment_clauses


def test_empty_input_returns_empty_list() -> None:
    assert segment_clauses("") == []
    assert segment_clauses("   \n\n  \t  ") == []


def test_numbered_clauses_split_on_markers() -> None:
    text = (
        "1. Term. This Agreement begins on the Effective Date.\n\n"
        "2. Liability. Neither party shall be liable for indirect damages.\n\n"
        "3. Confidentiality. Each party shall protect the other's data.\n\n"
        "4. Payment. Customer shall pay within thirty days.\n\n"
        "5. Termination. Either party may end this with notice."
    )
    segs = segment_clauses(text)
    assert len(segs) == 5
    assert segs[0].text.startswith("1. Term.")
    assert segs[4].text.startswith("5. Termination.")


def test_unstructured_paragraph_falls_back_to_sentences() -> None:
    """The case that previously returned 1 clause for 3 sentences."""
    text = (
        "Either party may terminate this Agreement upon thirty (30) days written notice. "
        "The Tenant shall pay $5,000 monthly. "
        "The information herein shall remain confidential."
    )
    segs = segment_clauses(text)
    assert len(segs) == 3
    assert "terminate" in segs[0].text
    assert "$5,000" in segs[1].text
    assert "confidential" in segs[2].text


def test_char_offsets_round_trip() -> None:
    """`text[s.start:s.end]` should reproduce each segment's original substring.

    Using a paragraph-fallback case where sentence offsets come from spaCy.
    """
    text = (
        "First sentence here. Second sentence after. Third sentence finally.\n\n"
        "Second paragraph with one sentence."
    )
    segs = segment_clauses(text)
    assert len(segs) >= 3
    for s in segs:
        assert text[s.start : s.end] == s.text or text[s.start : s.end].strip() == s.text


def test_mixed_marker_and_sentence_fallback() -> None:
    """Numbered items stay as units; only unstructured tail uses the sentencizer."""
    text = (
        "1. Liability. Damages limited to $1,000.\n\n"
        "Some unrelated commentary here. It spans two sentences."
    )
    segs = segment_clauses(text)
    # Two structural matches: the "1." numbered clause and the trailing paragraph.
    # The paragraph is multi-sentence so it should split into 2.
    texts = [s.text for s in segs]
    assert any(t.startswith("1. Liability") for t in texts)
    assert any("commentary" in t for t in texts)
    assert any("two sentences" in t for t in texts)


def test_single_sentence_paragraph_stays_single() -> None:
    text = "Just one sentence in this paragraph."
    segs = segment_clauses(text)
    assert len(segs) == 1
    assert segs[0].text == text


def test_max_clauses_caps_output() -> None:
    text = ". ".join(f"Sentence number {i}" for i in range(1, 21)) + "."
    segs = segment_clauses(text, max_clauses=5)
    assert len(segs) == 5


def test_segment_dataclass_fields() -> None:
    segs = segment_clauses("Hello world. Goodbye world.")
    assert all(isinstance(s, Segment) for s in segs)
    assert all(s.end > s.start for s in segs)
