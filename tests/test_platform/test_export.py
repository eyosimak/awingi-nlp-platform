"""
Unit & Integration Tests for Dataset Export Engine (GET /export and GET /api/export)
"""

import json
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
async def test_export_page_renders(client: AsyncClient):
    """Ensure the export configuration page renders HTML successfully."""
    response = await client.get("/export")
    assert response.status_code == 200
    assert "Dataset Partitioning" in response.text


@pytest.mark.asyncio
async def test_export_empty_corpus(client: AsyncClient):
    """Test export when database has no sentences matching filter."""
    response = await client.get("/api/export?status=all&domain=nonexistent_domain")
    assert response.status_code == 200
    assert response.headers.get("X-Total-Count") == "0"


@pytest.mark.asyncio
async def test_export_deterministic_splits_and_jsonl(client: AsyncClient, db: Session):
    """Verify deterministic dataset partitioning (train/val/test) into valid JSONL."""
    doc = Document(
        id=str(uuid.uuid4()),
        source_filename="agri_reader.pdf",
        doc_type="agriculture",
    )
    db.add(doc)

    test_domain = f"export_{uuid.uuid4().hex[:8]}"
    # Insert 10 approved sentences
    prefix = uuid.uuid4().hex[:8]
    for i in range(10):
        sent = Sentence(
            id=f"export-{prefix}-{i:03d}",
            document_id=doc.id,
            raw_text=f"Awingi sentence sample number {i}.",
            normalized_text=f"Awingi sentence sample number {i}.",
            language="awn",
            char_count=32,
            word_count=5,
            domain=test_domain,
            status="approved",
        )
        db.add(sent)
    db.commit()

    # Request export with 80% train, 10% val, 10% test
    response = await client.get(
        f"/api/export?status=approved&domain={test_domain}&train_ratio=0.8&val_ratio=0.1&seed=42"
    )
    assert response.status_code == 200
    assert response.headers.get("X-Train-Count") == "8"
    assert response.headers.get("X-Val-Count") == "1"
    assert response.headers.get("X-Test-Count") == "1"

    # Parse and validate JSONL records
    lines = [line.strip() for line in response.text.split("\n") if line.strip()]
    assert len(lines) == 10

    records = [json.loads(line) for line in lines]
    splits = [r["split"] for r in records]
    assert splits.count("train") == 8
    assert splits.count("val") == 1
    assert splits.count("test") == 1

    for r in records:
        assert "text" in r
        assert "language" in r
        assert r["language"] == "awn"
        assert r["domain"] == test_domain


@pytest.mark.asyncio
async def test_export_invalid_ratio_rejected(client: AsyncClient):
    """Ensure invalid split ratios exceeding 1.0 are rejected with 400 Bad Request."""
    response = await client.get("/api/export?train_ratio=0.8&val_ratio=0.3")
    assert response.status_code == 400
