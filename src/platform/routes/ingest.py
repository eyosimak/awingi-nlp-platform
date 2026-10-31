"""
Awingi NLP Platform — Document & Sentence Ingestion (API & Web UI)
Bridge for adding authentic Awingi corpus data via REST API or direct browser ingestion.
"""

import json
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from src.common.schemas import IngestionBatch
from src.platform.database import get_db
from src.platform.models import Document, Sentence
from src.platform.templates import templates
from src.platform.auth.dependencies import get_current_user_optional

router = APIRouter(tags=["ingestion"])


@router.get("/ingest", response_class=HTMLResponse)
async def ingest_page(
    request: Request,
    message: Optional[str] = None,
    error: Optional[str] = None,
    user=Depends(get_current_user_optional),
):
    """Render data ingestion UI for adding real documents and sentences."""
    return templates.TemplateResponse(
        request=request,
        name="ingest.html",
        context={
            "message": message,
            "error": error,
            "user": user,
        },
    )


@router.post("/ingest/manual")
async def ingest_manual_text(
    request: Request,
    source_filename: str = Form(...),
    title: str = Form(""),
    doc_type: str = Form("other"),
    domain: str = Form("general"),
    orthography_standard: str = Form("latin_official"),
    text_content: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    """
    Ingest authentic Awingi sentences directly from manual text input.
    Each non-empty line is normalized and stored as a pending sentence.
    """
    lines = [line.strip() for line in text_content.splitlines() if line.strip()]
    if not lines:
        return templates.TemplateResponse(
            request=request,
            name="ingest.html",
            context={"error": "Text content contains no valid non-empty lines.", "user": user},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    total_chars = sum(len(line) for line in lines)
    doc = Document(
        id=str(uuid.uuid4()),
        source_filename=source_filename.strip(),
        doc_type=doc_type.strip(),
        title=title.strip() if title else source_filename.strip(),
        total_characters=total_chars,
        total_raw_lines=len(lines),
        total_sentences=len(lines),
        extraction_status="success",
        pipeline_version="direct-input-0.1.0",
        batch_id=str(uuid.uuid4()),
    )
    db.add(doc)

    for line in lines:
        cleaned_text = " ".join(line.split())
        sentence = Sentence(
            id=str(uuid.uuid4()),
            document_id=doc.id,
            raw_text=line,
            normalized_text=cleaned_text,
            language="awn",
            char_count=len(cleaned_text),
            word_count=len(cleaned_text.split()),
            domain=domain.strip(),
            orthography_standard=orthography_standard.strip(),
            status="pending",
        )
        db.add(sentence)

    db.commit()
    return RedirectResponse(
        url=f"/review?status=pending&domain={domain.strip()}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/ingest/upload")
async def ingest_upload_file(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    """
    Upload and parse an IngestionBatch JSON file directly via the web interface.
    """
    try:
        content = await file.read()
        data = json.loads(content.decode("utf-8"))
        batch = IngestionBatch.model_validate(data)

        doc_type_val = (
            batch.document.doc_type.value
            if hasattr(batch.document.doc_type, "value")
            else str(batch.document.doc_type)
        )
        status_val = (
            batch.document.extraction_status.value
            if hasattr(batch.document.extraction_status, "value")
            else str(batch.document.extraction_status)
        )

        doc = Document(
            id=str(uuid.uuid4()),
            source_filename=batch.document.source_filename,
            doc_type=doc_type_val,
            title=batch.document.title or "",
            total_characters=batch.document.total_characters,
            total_raw_lines=batch.document.total_raw_lines,
            total_sentences=len(batch.sentences),
            extraction_status=status_val,
            error_log=batch.document.error_log,
            pipeline_version=batch.pipeline_version,
            batch_id=batch.batch_id,
        )
        db.add(doc)

        added = 0
        for sent in batch.sentences:
            if sent.is_duplicate:
                continue
            sentence = Sentence(
                id=str(uuid.uuid4()),
                document_id=doc.id,
                raw_text=sent.raw_text,
                normalized_text=sent.normalized_text,
                language=sent.language or "awn",
                char_count=sent.char_count,
                word_count=sent.word_count,
                is_duplicate=sent.is_duplicate,
                duplicate_of_id=sent.duplicate_of_id,
                orthography_standard=sent.orthography_standard or "latin_official",
                domain=sent.domain or "general",
                status="pending",
            )
            db.add(sentence)
            added += 1

        db.commit()
        return RedirectResponse(
            url=f"/review?status=pending",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            request=request,
            name="ingest.html",
            context={"error": f"Failed to parse or ingest batch JSON: {str(e)}", "user": user},
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@router.post("/api/ingest", status_code=status.HTTP_200_OK)
async def ingest_batch(batch: IngestionBatch, db: Session = Depends(get_db)):
    """
    Accept a batch of cleaned sentences from Computer 2's pipeline.
    Validates strictly against the shared Pydantic contract (src.common.schemas)
    and persists Document and Sentence records in the database.
    """
    try:
        doc_type_val = (
            batch.document.doc_type.value
            if hasattr(batch.document.doc_type, "value")
            else str(batch.document.doc_type)
        )
        status_val = (
            batch.document.extraction_status.value
            if hasattr(batch.document.extraction_status, "value")
            else str(batch.document.extraction_status)
        )

        doc = Document(
            id=str(uuid.uuid4()),
            source_filename=batch.document.source_filename,
            doc_type=doc_type_val,
            title=batch.document.title or "",
            total_characters=batch.document.total_characters,
            total_raw_lines=batch.document.total_raw_lines,
            total_sentences=len(batch.sentences),
            extraction_status=status_val,
            error_log=batch.document.error_log,
            pipeline_version=batch.pipeline_version,
            batch_id=batch.batch_id,
        )
        db.add(doc)

        added = 0
        skipped = 0

        for sent in batch.sentences:
            if sent.is_duplicate:
                skipped += 1
                continue

            sentence = Sentence(
                id=str(uuid.uuid4()),
                document_id=doc.id,
                raw_text=sent.raw_text,
                normalized_text=sent.normalized_text,
                language=sent.language or "awn",
                char_count=sent.char_count,
                word_count=sent.word_count,
                is_duplicate=sent.is_duplicate,
                duplicate_of_id=sent.duplicate_of_id,
                orthography_standard=sent.orthography_standard or "latin_official",
                domain=sent.domain or "general",
                status="pending",
            )
            db.add(sentence)
            added += 1

        db.commit()

        return {
            "status": "success",
            "document_id": doc.id,
            "sentences_added": added,
            "duplicates_skipped": skipped,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest batch: {str(e)}",
        )
