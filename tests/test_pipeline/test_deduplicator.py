"""
Unit Tests for Exact Deduplication Engine
=========================================
Validates exact sentence deduplication, case-insensitivity, duplicate linking,
and session tracking across documents.
"""

from src.pipeline.deduplicator import Deduplicator


def test_deduplicator_first_occurrence():
    """Verify first occurrence is marked not duplicate."""
    dedup = Deduplicator()
    sent = dedup.process_sentence(
        raw_text="Awi agawxi qutɨrsɨ.",
        normalized_text="Awi agawxi qutɨrsɨ.",
        sentence_id="sent-001",
    )
    assert sent.is_duplicate is False
    assert sent.duplicate_of_id is None
    assert sent.word_count == 3
    assert sent.char_count == 19


def test_deduplicator_duplicate_detected():
    """Verify second identical sentence is marked duplicate and linked to first occurrence."""
    dedup = Deduplicator()
    first = dedup.process_sentence(
        raw_text="Awi agawxi qutɨrsɨ.",
        normalized_text="Awi agawxi qutɨrsɨ.",
        sentence_id="sent-001",
    )
    second = dedup.process_sentence(
        raw_text="Awi  agawxi   qutɨrsɨ.",
        normalized_text="Awi agawxi qutɨrsɨ.",
        sentence_id="sent-002",
    )
    assert first.is_duplicate is False
    assert second.is_duplicate is True
    assert second.duplicate_of_id == "sent-001"


def test_deduplicator_case_insensitivity():
    """Verify case differences in normalized text are recognized as duplicates."""
    dedup = Deduplicator()
    first = dedup.process_sentence(
        raw_text="awi agawxi qutɨrsɨ.",
        normalized_text="awi agawxi qutɨrsɨ.",
        sentence_id="sent-lower",
    )
    second = dedup.process_sentence(
        raw_text="Awi Agawxi Qutɨrsɨ.",
        normalized_text="Awi Agawxi Qutɨrsɨ.",
        sentence_id="sent-title",
    )
    assert first.is_duplicate is False
    assert second.is_duplicate is True
    assert second.duplicate_of_id == "sent-lower"


def test_deduplicator_cross_document_tracking():
    """Verify deduplication works across different documents in a session."""
    dedup = Deduplicator()
    doc1_sent = dedup.process_sentence(
        raw_text="Anbaŋ bɨsta antɨrsɨ.",
        normalized_text="Anbaŋ bɨsta antɨrsɨ.",
        document_id="book-1",
        sentence_id="book1-s1",
    )
    doc2_sent = dedup.process_sentence(
        raw_text="Anbaŋ bɨsta antɨrsɨ.",
        normalized_text="Anbaŋ bɨsta antɨrsɨ.",
        document_id="book-2",
        sentence_id="book2-s1",
    )
    assert doc1_sent.is_duplicate is False
    assert doc2_sent.is_duplicate is True
    assert doc2_sent.duplicate_of_id == "book1-s1"


def test_deduplicator_reset():
    """Verify reset clears seen hashes."""
    dedup = Deduplicator()
    dedup.process_sentence(
        raw_text="Awi agawxi.",
        normalized_text="Awi agawxi.",
        sentence_id="s1",
    )
    dedup.reset()
    again = dedup.process_sentence(
        raw_text="Awi agawxi.",
        normalized_text="Awi agawxi.",
        sentence_id="s2",
    )
    assert again.is_duplicate is False
