"""
Unit & Integration Tests for Reviewer QA System (GET & POST /review)
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


@pytest.fixture
def sample_sentence(db: Session) -> Sentence:
    doc = Document(
        id=str(uuid.uuid4()),
        source_filename="test_reader.pdf",
        doc_type="textbook",
        title="Test Reader",
    )
    db.add(doc)

    sent = Sentence(
        id=str(uuid.uuid4()),
        document_id=doc.id,
        raw_text="Awi agawxi qutɨrsɨ.",
        normalized_text="Awi agawxi qutɨrsɨ.",
        language="awn",
        char_count=19,
        word_count=3,
        domain="education",
        status="pending",
    )
    db.add(sent)
    db.commit()
    db.refresh(sent)
    return sent


@pytest.mark.asyncio
async def test_review_page_renders_html(client: AsyncClient, sample_sentence: Sentence):
    """Ensure the review dashboard HTML page renders with status 200."""
    response = await client.get("/review?status=pending")
    assert response.status_code == 200
    assert "Awingi Corpus Review" in response.text
    assert sample_sentence.normalized_text in response.text


@pytest.mark.asyncio
async def test_approve_sentence(client: AsyncClient, sample_sentence: Sentence, db: Session):
    """Verify that approving a sentence updates its status in the database."""
    sent_id = sample_sentence.id
    response = await client.post(
        f"/review/{sent_id}/approve",
        data={"return_url": "/review"},
        follow_redirects=False,
    )
    assert response.status_code == 303

    db.expire_all()
    updated = db.query(Sentence).filter(Sentence.id == sent_id).first()
    assert updated.status == "approved"
    assert updated.reviewed_at is not None


@pytest.mark.asyncio
async def test_flag_sentence_with_note(client: AsyncClient, sample_sentence: Sentence, db: Session):
    """Verify that flagging a sentence persists reviewer notes and flagged status."""
    sent_id = sample_sentence.id
    note_text = "Suspected orthographic inconsistency in barred-i."
    response = await client.post(
        f"/review/{sent_id}/flag",
        data={"note": note_text, "return_url": "/review"},
        follow_redirects=False,
    )
    assert response.status_code == 303

    db.expire_all()
    updated = db.query(Sentence).filter(Sentence.id == sent_id).first()
    assert updated.status == "flagged"
    assert updated.reviewer_note == note_text


@pytest.mark.asyncio
async def test_edit_sentence_and_approve(client: AsyncClient, sample_sentence: Sentence, db: Session):
    """Verify that editing normalized text recalculates counts and approves sentence."""
    sent_id = sample_sentence.id
    corrected = "Awi agawxi qutɨrsɨ kɨda."
    response = await client.post(
        f"/review/{sent_id}/edit",
        data={"normalized_text": corrected, "return_url": "/review"},
        follow_redirects=False,
    )
    assert response.status_code == 303

    db.expire_all()
    updated = db.query(Sentence).filter(Sentence.id == sent_id).first()
    assert updated.normalized_text == corrected
    assert updated.char_count == len(corrected)
    assert updated.word_count == 4
    assert updated.status == "approved"
