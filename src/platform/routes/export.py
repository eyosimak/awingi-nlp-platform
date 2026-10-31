"""
Awingi NLP Platform — Dataset Export Engine
Generates reproducible, leak-free train/validation/test splits formatted as JSONL
for SentencePiece tokenizer training and language model fine-tuning.
"""

import io
import json
import random
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlalchemy.orm import Session
from src.platform.database import get_db
from src.platform.models import Sentence
from src.platform.templates import templates
from src.platform.auth.dependencies import get_current_user_optional

router = APIRouter(tags=["export"])


@router.get("/export", response_class=HTMLResponse)
async def export_page(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    """
    Renders export configuration interface showing corpus availability and split settings.
    """
    approved_count = db.query(Sentence).filter(
        Sentence.is_duplicate == False, Sentence.status == "approved"
    ).count()
    total_count = db.query(Sentence).filter(Sentence.is_duplicate == False).count()

    domains = [
        row[0]
        for row in db.query(Sentence.domain)
        .filter(Sentence.is_duplicate == False)
        .distinct()
        .all()
        if row[0]
    ]

    return templates.TemplateResponse(
        request=request,
        name="export.html",
        context={
            "approved_count": approved_count,
            "total_count": total_count,
            "domains": sorted(domains),
            "user": user,
        },
    )


@router.get("/api/export")
async def export_corpus(
    format: str = Query(default="jsonl"),
    status_filter: str = Query(default="approved", alias="status"),
    domain: str = Query(default="all"),
    train_ratio: float = Query(default=0.8, ge=0.0, le=1.0),
    val_ratio: float = Query(default=0.1, ge=0.0, le=1.0),
    seed: int = Query(default=42),
    persist_splits: bool = Query(default=True),
    db: Session = Depends(get_db),
):
    """
    Export dataset as JSONL with deterministic train/val/test splits.
    Guarantees no data leakage across splits via pseudo-random seed shuffling.
    Optionally persists the split assignment to the database.
    """
    if train_ratio + val_ratio > 1.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The sum of train_ratio and val_ratio cannot exceed 1.0",
        )

    query = db.query(Sentence).filter(Sentence.is_duplicate == False)

    if status_filter == "approved":
        query = query.filter(Sentence.status == "approved")
    elif status_filter != "all":
        query = query.filter(Sentence.status == status_filter)

    if domain != "all":
        query = query.filter(Sentence.domain == domain)

    # Deterministic sorting by ID first to ensure order is stable across platforms
    sentences = query.order_by(Sentence.id).all()
    n = len(sentences)

    # Shuffle deterministically using provided seed
    rng = random.Random(seed)
    indices = list(range(n))
    rng.shuffle(indices)

    train_end = int(n * train_ratio)
    val_end = train_end + int(n * val_ratio)

    splits = {
        "train": [sentences[i] for i in indices[:train_end]],
        "val": [sentences[i] for i in indices[train_end:val_end]],
        "test": [sentences[i] for i in indices[val_end:]],
    }

    if persist_splits and n > 0:
        for split_name, split_sents in splits.items():
            for s in split_sents:
                s.split = split_name
        db.commit()

    # Build streaming JSONL output
    output = io.StringIO()
    for split_name, split_sents in splits.items():
        for sent in split_sents:
            record = {
                "id": sent.id,
                "text": sent.normalized_text,
                "raw_text": sent.raw_text,
                "language": sent.language,
                "domain": sent.domain,
                "orthography_standard": sent.orthography_standard,
                "split": split_name,
                "word_count": sent.word_count,
                "char_count": sent.char_count,
                "document_id": sent.document_id,
            }
            output.write(json.dumps(record, ensure_ascii=False) + "\n")

    output.seek(0)
    filename = f"awingi_corpus_{status_filter}_{n}_sentences.jsonl"

    return StreamingResponse(
        output,
        media_type="application/x-ndjson",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Train-Count": str(len(splits["train"])),
            "X-Val-Count": str(len(splits["val"])),
            "X-Test-Count": str(len(splits["test"])),
            "X-Total-Count": str(n),
        },
    )
