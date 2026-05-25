"""Tests for the regex-based NER extractors."""

from __future__ import annotations

from app.pipeline.ner import extract_entities


def _types(text: str) -> set[str]:
    return {e.type for e in extract_entities(text)}


def test_extracts_date_and_amount() -> None:
    text = "Customer shall pay $5,000 within thirty (30) days."
    types = _types(text)
    assert "AMOUNT" in types
    assert "DATE" in types
    assert "OBLIGATION" in types  # "shall pay"


def test_party_captures_role_only() -> None:
    text = "the Tenant shall vacate the premises."
    entities = extract_entities(text)
    parties = [e for e in entities if e.type == "PARTY"]
    assert len(parties) == 1
    assert parties[0].text == "Tenant"
    # Span should be just over "Tenant", not "the Tenant"
    assert text[parties[0].start : parties[0].end] == "Tenant"


def test_obligation_requires_action_verb_after_shall() -> None:
    """Bare 'shall' must NOT be tagged on its own."""
    text = "This Agreement shall be governed by Delaware law."
    types = _types(text)
    # "shall be" alone is too generic; only verb-of-action patterns trigger.
    assert "OBLIGATION" not in types


def test_obligation_fires_on_must_and_required_to() -> None:
    text = "The receiving party must protect Confidential Information; "
    text += "The Customer is required to notify the Company of any breach."
    types = _types(text)
    assert "OBLIGATION" in types


def test_right_pattern_matches_right_to_phrase() -> None:
    text = "The Customer shall have the right to audit the Company's records."
    entities = extract_entities(text)
    rights = [e for e in entities if e.type == "RIGHT"]
    assert len(rights) >= 1
    assert any("right to audit" in r.text.lower() for r in rights)


def test_right_pattern_matches_may_with_action_verb() -> None:
    text = "Either party may terminate this Agreement upon notice."
    types = _types(text)
    assert "RIGHT" in types


def test_condition_in_the_event_of() -> None:
    text = "In the event of a material breach by the Customer, the Company may terminate."
    types = _types(text)
    assert "CONDITION" in types


def test_condition_subject_to_and_provided_that() -> None:
    text = (
        "Either party may assign this Agreement subject to the prior written consent "
        "of the other party, provided that the assignment does not increase liabilities."
    )
    types = _types(text)
    assert "CONDITION" in types
    # Both subject-to and provided-that should be picked up
    conditions = [e for e in extract_entities(text) if e.type == "CONDITION"]
    assert len(conditions) >= 2


def test_no_conditions_in_plain_prose() -> None:
    """Plain narrative shouldn't accidentally trip CONDITION."""
    text = "The Customer shall pay invoices within thirty days of receipt."
    types = _types(text)
    assert "CONDITION" not in types


def test_offsets_round_trip() -> None:
    text = (
        "In the event of breach, the Customer shall pay $5,000 within seven (7) days "
        "and may terminate the Agreement subject to thirty (30) days written notice."
    )
    for e in extract_entities(text):
        # Each span should reproduce the entity text from the original input
        assert text[e.start : e.end].lower().startswith(e.text.lower()[:5])


def test_entities_sorted_by_position() -> None:
    text = "the Customer shall pay $5,000 within thirty (30) days."
    entities = extract_entities(text)
    starts = [e.start for e in entities]
    assert starts == sorted(starts)
