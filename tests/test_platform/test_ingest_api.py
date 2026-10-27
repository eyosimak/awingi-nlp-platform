"""
Unit & Integration Tests for Ingestion API (POST /api/ingest)
"""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session
from src.platform.app import app
from src.platform.database import SessionLocal
from src.platform.models import Document, Sentence


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_ingest_valid_batch(client: AsyncClient, db: Session):
    """Verify that a valid IngestionBatch is successfully ingested and stored."""
    payload = {
        "document": {
            "source_filename": "awi_grade4_reader.pdf",
            "doc_type": "textbook",
            "title": "Awi Agawxi Grade 4 Reader",
            "total_characters": 1200,
            "total_raw_lines": 50,
            "extraction_status": "success",
        },
        "sentences": [
            {
                "raw_text": "Awi  agawxi   qutɨrsɨ.",
                "normalized_text": "Awi agawxi qutɨrsɨ.",
                "language": "awn",
                "char_count": 19,
                "word_count": 3,
                "is_duplicate": False,
                "domain": "education",
            }
        ],
        "batch_id": "11111111-2222-3333-4444-555555555555",
        "pipeline_version": "0.1.0",
    }

    response = await client.post("/api/ingest", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["sentences_added"] == 1
    assert data["duplicates_skipped"] == 0

    # Verify database persistence
    doc = db.query(Document).filter(Document.id == data["document_id"]).first()
    assert doc is not None
    assert doc.source_filename == "awi_grade4_reader.pdf"

    sent = db.query(Sentence).filter(Sentence.document_id == doc.id).first()
    assert sent is not None
    assert sent.normalized_text == "Awi agawxi qutɨrsɨ."
    assert "ɨ" in sent.normalized_text


@pytest.mark.asyncio
async def test_ingest_duplicate_skipping(client: AsyncClient):
    """Verify that sentences marked is_duplicate=True are filtered out during ingestion."""
    payload = {
        "document": {
            "source_filename": "awi_agri_guide.docx",
            "doc_type": "agriculture",
            "title": "Awingi Potato Cultivation",
            "total_characters": 500,
            "total_raw_lines": 20,
            "extraction_status": "success",
        },
        "sentences": [
            {
                "raw_text": "Dɨnxɨwa kɨda agawxi.",
                "normalized_text": "Dɨnxɨwa kɨda agawxi.",
                "language": "awn",
                "char_count": 21,
                "word_count": 3,
                "is_duplicate": False,
                "domain": "agriculture",
            },
            {
                "raw_text": "Dɨnxɨwa kɨda agawxi.",
                "normalized_text": "Dɨnxɨwa kɨda agawxi.",
                "language": "awn",
                "char_count": 21,
                "word_count": 3,
                "is_duplicate": True,
                "duplicate_of_id": "sent-001",
                "domain": "agriculture",
            },
        ],
        "batch_id": "22222222-3333-4444-5555-666666666666",
        "pipeline_version": "0.1.0",
    }

    response = await client.post("/api/ingest", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["sentences_added"] == 1
    assert data["duplicates_skipped"] == 1


@pytest.mark.asyncio
async def test_ingest_unicode_preservation(client: AsyncClient):
    """Ensure non-ASCII Cushitic Latin characters (ɨ, ŋ) and glottal stops are preserved."""
    payload = {
        "document": {
            "source_filename": "phonology_sample.txt",
            "doc_type": "literature",
            "title": "Awingi Phonetics",
            "total_characters": 100,
            "total_raw_lines": 5,
            "extraction_status": "success",
        },
        "sentences": [
            {
                "raw_text": "Anbaŋ  bɨsta antɨrsɨ.",
                "normalized_text": "Anbaŋ bɨsta antɨrsɨ.",
                "language": "awn",
                "char_count": 20,
                "word_count": 3,
                "is_duplicate": False,
                "domain": "general",
            }
        ],
        "batch_id": "33333333-4444-5555-6666-777777777777",
        "pipeline_version": "0.1.0",
    }

    response = await client.post("/api/ingest", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["sentences_added"] == 1


@pytest.mark.asyncio
async def test_ingest_invalid_payload_rejected(client: AsyncClient):
    """Verify that payloads violating the shared Pydantic contract are rejected with 422."""
    invalid_payload = {
        "document": {
            "source_filename": "incomplete.pdf"
            # Missing required fields or improper types
        },
        "sentences": "not-a-list",
    }
    response = await client.post("/api/ingest", json=invalid_payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ingest_page_renders(client: AsyncClient):
    """Ensure the web ingestion page renders successfully."""
    response = await client.get("/ingest")
    assert response.status_code == 200
    assert "Add Real Corpus Data" in response.text
    assert "Direct Sentence Ingestion" in response.text


@pytest.mark.asyncio
async def test_ingest_manual_text(client: AsyncClient, db: Session):
    """Ensure users can directly paste real sentences via the web UI."""
    data = {
        "source_filename": "manual_real_input.txt",
        "title": "Awi Field Notes",
        "doc_type": "agriculture",
        "domain": "agriculture",
        "orthography_standard": "latin_official",
        "text_content": "Awi agawxi qutɨrsɨ.\nDɨnxɨwa kɨda agawxi.\n\nAnbaŋ bɨsta antɨrsɨ.",
    }
    response = await client.post("/ingest/manual", data=data, follow_redirects=False)
    assert response.status_code == 303
    assert "/review" in response.headers.get("location")

    doc = db.query(Document).filter(Document.source_filename == "manual_real_input.txt").first()
    assert doc is not None
    assert doc.total_sentences == 3

    sents = db.query(Sentence).filter(Sentence.document_id == doc.id).all()
    assert len(sents) == 3
    assert any("ɨ" in s.normalized_text for s in sents)
