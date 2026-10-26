"""
Awingi NLP Platform — Shared Interface Contract
================================================

CRITICAL ARCHITECTURAL RULE:
This file is the single source of truth shared between:
  - Computer 1 (Platform & ML Lead: src/platform/ and src/ml/)
  - Computer 2 (Ingestion & Pipeline Lead: src/pipeline/)

DO NOT modify, rename, or delete models or fields in this file
without explicit coordination and consensus across both computers.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Categorization of source documents provided by the Institute of Agaw Studies."""
    TEXTBOOK = "textbook"
    LITERATURE = "literature"
    CURRICULUM = "curriculum"
    AGRICULTURE = "agriculture"
    RELIGIOUS = "religious"
    DICTIONARY = "dictionary"
    OTHER = "other"


class ExtractionStatus(str, Enum):
    """Execution status of document extraction by Computer 2 pipeline."""
    SUCCESS = "success"
    PARTIAL = "partial_error"
    FAILED = "failed"


class ReviewStatus(str, Enum):
    """Human-in-the-loop validation status on Computer 1 web platform."""
    PENDING = "pending"
    APPROVED = "approved"
    FLAGGED = "flagged"
    REJECTED = "rejected"


class ExtractedDocument(BaseModel):
    """
    Metadata representation of a source file processed by Computer 2's ingestion pipeline.
    """
    source_filename: str = Field(..., description="Original filename (e.g., 'grade4_reader.pdf')")
    doc_type: DocumentType = Field(default=DocumentType.OTHER, description="Identified or user-tagged document category")
    title: str = Field(default="", description="Human-readable title of the book or article")
    total_characters: int = Field(default=0, ge=0, description="Total characters extracted prior to cleaning")
    total_raw_lines: int = Field(default=0, ge=0, description="Total non-empty lines extracted")
    extraction_status: ExtractionStatus = Field(default=ExtractionStatus.SUCCESS, description="Status code of extraction")
    error_log: Optional[str] = Field(default=None, description="Diagnostic error trace if status is not success")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="UTC timestamp of extraction")


class CleanedSentence(BaseModel):
    """
    Standardized representation of a single normalized sentence produced by Computer 2.
    """
    document_id: Optional[str] = Field(default=None, description="Reference ID of the parent document")
    raw_text: str = Field(..., min_length=1, description="Original uncleaned extracted text line")
    normalized_text: str = Field(..., min_length=1, description="Text after Unicode NFKC and Awingi orthography normalization")
    language: str = Field(default="awn", description="ISO 639-3 language identifier for Awingi")
    char_count: int = Field(..., ge=1, description="Character count of normalized text")
    word_count: int = Field(..., ge=1, description="Word count of normalized text")
    is_duplicate: bool = Field(default=False, description="Flag indicating if sentence is duplicate within corpus")
    duplicate_of_id: Optional[str] = Field(default=None, description="ID or hash of the first occurrence if duplicate")
    orthography_standard: str = Field(default="latin_official", description="Orthography variant (e.g. latin_official, geez_archival)")
    domain: str = Field(default="general", description="Semantic domain: general, agriculture, education, religion")


class IngestionBatch(BaseModel):
    """
    Payload contract representing a complete document extraction batch transmitted
    from Computer 2's pipeline to Computer 1's web platform (via REST API or JSON export).
    """
    document: ExtractedDocument
    sentences: List[CleanedSentence] = Field(default_factory=list)
    batch_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique UUID for this ingestion batch")
    pipeline_version: str = Field(default="0.1.0", description="SemVer version of Computer 2's pipeline")
    exported_at: datetime = Field(default_factory=datetime.utcnow, description="UTC timestamp of batch export")
