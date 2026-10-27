"""
Unit & Integration Tests for Main Corpus Dashboard (GET /)
"""

import uuid
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
async def test_dashboard_renders(client: AsyncClient):
    """Ensure dashboard homepage renders with 200 OK."""
    response = await client.get("/")
    assert response.status_code == 200
    assert "Awingi Language Model" in response.text
    assert "Unique Sentences" in response.text


@pytest.mark.asyncio
async def test_dashboard_statistics_aggregation(client: AsyncClient, db: Session):
    """Verify aggregated metrics for sentences, words, and domains."""
    doc = Document(
        id=str(uuid.uuid4()),
        source_filename="agri_primer.pdf",
        doc_type="agriculture",
        title="Agri Primer",
        total_characters=200,
        total_raw_lines=10,
        total_sentences=2,
    )
    db.add(doc)

    s1 = Sentence(
        id=str(uuid.uuid4()),
        document_id=doc.id,
        raw_text="Dɨnxɨwa kɨda agawxi.",
        normalized_text="Dɨnxɨwa kɨda agawxi.",
        language="awn",
        char_count=21,
        word_count=3,
        domain="agriculture",
        status="approved",
    )
    s2 = Sentence(
        id=str(uuid.uuid4()),
        document_id=doc.id,
        raw_text="Anbaŋ bɨsta antɨrsɨ.",
        normalized_text="Anbaŋ bɨsta antɨrsɨ.",
        language="awn",
        char_count=20,
        word_count=3,
        domain="general",
        status="pending",
    )
    db.add_all([s1, s2])
    db.commit()

    response = await client.get("/")
    assert response.status_code == 200
    # Both domains should appear in output
    assert "agriculture" in response.text.lower()
    assert "general" in response.text.lower()
