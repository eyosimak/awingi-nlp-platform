"""
Contract & Schema Integrity Verification Tests
==============================================
Validates that the shared Pydantic models in src/common/schemas.py
correctly parse, validate, and serialize Awingi language data payloads.
"""

from datetime import datetime
from src.common.schemas import (
    IngestionBatch,
    ExtractedDocument,
    CleanedSentence,
    DocumentType,
    ExtractionStatus,
)


def test_schema_parsing_from_fixture(sample_ingestion_batch: IngestionBatch):
    """Test that sample_batch.json strictly validates against IngestionBatch."""
    batch = sample_ingestion_batch
    assert batch.pipeline_version == "0.1.0"
    assert batch.document.source_filename == "sample_reader_grade3.pdf"
    assert batch.document.doc_type == DocumentType.TEXTBOOK
    assert len(batch.sentences) == 3


def test_awingi_special_characters_preservation(sample_ingestion_batch: IngestionBatch):
    """Ensure Awingi special characters (ɨ, ŋ) are preserved in normalized sentences."""
    sentences = sample_ingestion_batch.sentences
    all_text = " ".join([s.normalized_text for s in sentences])
    
    # Must preserve barred-i
    assert "ɨ" in all_text, "Awingi barred-i (ɨ) was lost in schema validation"
    # Must preserve eng
    assert "ŋ" in all_text, "Awingi eng (ŋ) was lost in schema validation"


def test_ingestion_batch_serialization_roundtrip(sample_ingestion_batch: IngestionBatch):
    """Ensure serialization to JSON and back produces identical data."""
    json_str = sample_ingestion_batch.model_dump_json()
    reconstructed = IngestionBatch.model_validate_json(json_str)
    assert reconstructed.batch_id == sample_ingestion_batch.batch_id
    assert len(reconstructed.sentences) == len(sample_ingestion_batch.sentences)
    assert reconstructed.document.title == sample_ingestion_batch.document.title


def test_manual_cleaned_sentence_creation():
    """Verify manual construction of CleanedSentence with Awingi Latin characters."""
    sent = CleanedSentence(
        raw_text="Awi agawxi qutɨrsɨ.",
        normalized_text="Awi agawxi qutɨrsɨ.",
        language="awn",
        char_count=19,
        word_count=3,
        domain="education",
    )
    assert sent.language == "awn"
    assert sent.char_count == 19
    assert sent.is_duplicate is False
