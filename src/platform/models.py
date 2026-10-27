"""
Awingi NLP Platform — SQLAlchemy ORM Data Models
"""

import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from src.platform.database import Base


class User(Base):
    """
    Platform user model supporting role-based access for students and reviewers.
    Roles:
      - 'admin': Full administrative control, user management, and dataset exports
      - 'reviewer': Capable of approving, flagging, and editing sentences in /review
      - 'contributor': Read-only access to dashboard statistics
    """
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="contributor")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    reviewed_sentences = relationship("Sentence", back_populates="reviewer", foreign_keys="Sentence.reviewed_by")


class Document(Base):
    """
    Metadata representation of an ingested source document (textbook, reader, etc.).
    Maintained in sync with ExtractedDocument from src.common.schemas.
    """
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_filename = Column(String(500), nullable=False)
    doc_type = Column(String(50), default="other")
    title = Column(String(500), default="")
    total_characters = Column(Integer, default=0)
    total_raw_lines = Column(Integer, default=0)
    total_sentences = Column(Integer, default=0)
    extraction_status = Column(String(20), default="success")
    error_log = Column(Text, nullable=True)
    pipeline_version = Column(String(20), default="0.1.0")
    batch_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    sentences = relationship("Sentence", back_populates="document", cascade="all, delete-orphan")


class Sentence(Base):
    """
    Individual sentence record extracted from source documents.
    Tracks Awingi linguistic normalization, deduplication, review state,
    and assigned dataset partition (train / val / test).
    """
    __tablename__ = "sentences"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=True, index=True)
    raw_text = Column(Text, nullable=False)
    normalized_text = Column(Text, nullable=False)
    language = Column(String(10), default="awn")
    char_count = Column(Integer, default=0)
    word_count = Column(Integer, default=0)
    is_duplicate = Column(Boolean, default=False, index=True)
    duplicate_of_id = Column(String(36), nullable=True)
    orthography_standard = Column(String(30), default="latin_official")
    domain = Column(String(30), default="general", index=True)

    # Human Review Workflow
    status = Column(String(20), default="pending", index=True)  # pending, approved, flagged, rejected
    reviewed_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    reviewer_note = Column(Text, nullable=True)

    # Dataset Partitioning
    split = Column(String(10), nullable=True, index=True)  # train, val, test
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="sentences")
    reviewer = relationship("User", back_populates="reviewed_sentences", foreign_keys=[reviewed_by])
