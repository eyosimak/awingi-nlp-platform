"""
Shared pytest configuration and test fixtures for Awingi NLP Platform.
"""

import json
from pathlib import Path
import pytest
from src.common.schemas import IngestionBatch, ExtractedDocument, CleanedSentence, DocumentType, ExtractionStatus


@pytest.fixture
def project_root() -> Path:
    """Return the absolute path of the project root."""
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def sample_batch_path(project_root: Path) -> Path:
    """Return path to the sample batch JSON fixture."""
    return project_root / "scripts" / "sample_data" / "sample_batch.json"


@pytest.fixture
def sample_batch_data(sample_batch_path: Path) -> dict:
    """Return parsed dictionary from sample_batch.json."""
    with open(sample_batch_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def sample_ingestion_batch(sample_batch_data: dict) -> IngestionBatch:
    """Return validated IngestionBatch instance."""
    return IngestionBatch.model_validate(sample_batch_data)
