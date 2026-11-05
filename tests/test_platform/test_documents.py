"""
Unit & Integration Tests for Document Management & Deduplication (GET & POST /documents)
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
async def test_documents_page_renders_html(client: AsyncClient, db: Session):
    """Ensure the document management page renders with 200 status and lists existing documents."""
    doc = Document(
        id=str(uuid.uuid4()),
        source_filename="agew_sample_doc.pdf",
        doc_type="textbook",
        title="Agew Sample Document",
    )
    db.add(doc)
    db.commit()

    response = await client.get("/documents")
    assert response.status_code == 200
    assert "Source Document Catalog" in response.text
    assert "agew_sample_doc.pdf" in response.text


@pytest.mark.asyncio
async def test_delete_document_cascades(client: AsyncClient, db: Session):
    """Ensure deleting a document also deletes attached sentences."""
    doc_id = str(uuid.uuid4())
    doc = Document(
        id=doc_id,
        source_filename="to_delete.txt",
        doc_type="other",
        title="To Delete",
    )
    db.add(doc)

    sent = Sentence(
        id=str(uuid.uuid4()),
        document_id=doc_id,
        raw_text="Sent to be deleted.",
        normalized_text="Sent to be deleted.",
        language="awn",
        char_count=19,
        word_count=4,
        status="pending",
    )
    db.add(sent)
    db.commit()

    response = await client.post(f"/documents/{doc_id}/delete", follow_redirects=False)
    assert response.status_code == 303

    db.expire_all()
    assert db.query(Document).filter(Document.id == doc_id).first() is None
    assert db.query(Sentence).filter(Sentence.document_id == doc_id).first() is None


@pytest.mark.asyncio
async def test_deduplicate_documents(client: AsyncClient, db: Session):
    """Ensure deduplication retains the document with most approvals and removes duplicate runs."""
    shared_filename = f"duplicate_reader_{uuid.uuid4().hex[:8]}.txt"

    # Doc 1: has 1 approved sentence
    doc1 = Document(
        id=str(uuid.uuid4()),
        source_filename=shared_filename,
        doc_type="reader",
        title="Reader Copy 1",
    )
    db.add(doc1)
    sent1 = Sentence(
        id=str(uuid.uuid4()),
        document_id=doc1.id,
        raw_text="Approved sentence.",
        normalized_text="Approved sentence.",
        language="awn",
        char_count=18,
        word_count=2,
        status="approved",
    )
    db.add(sent1)

    # Doc 2: has 0 approved sentences (pending only)
    doc2 = Document(
        id=str(uuid.uuid4()),
        source_filename=shared_filename,
        doc_type="reader",
        title="Reader Copy 2",
    )
    db.add(doc2)
    sent2 = Sentence(
        id=str(uuid.uuid4()),
        document_id=doc2.id,
        raw_text="Pending sentence.",
        normalized_text="Pending sentence.",
        language="awn",
        char_count=17,
        word_count=2,
        status="pending",
    )
    db.add(sent2)
    db.commit()

    doc1_id = doc1.id
    doc2_id = doc2.id

    # Trigger deduplication
    response = await client.post("/documents/deduplicate", follow_redirects=False)
    assert response.status_code == 303

    db.expire_all()
    remaining = db.query(Document).filter(Document.source_filename == shared_filename).all()
    assert len(remaining) == 1
    assert remaining[0].id == doc1_id
