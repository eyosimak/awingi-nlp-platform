"""
Awingi NLP Platform — Reviewer Quality Assurance Dashboard
Enables human-in-the-loop review, approval, flagging, and inline corrections
for extracted Awingi sentences.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Form, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
from src.platform.database import get_db
from src.platform.models import Document, Sentence
from src.platform.templates import templates
from src.platform.auth.dependencies import get_current_user_optional

router = APIRouter(tags=["review"])


@router.get("/review", response_class=HTMLResponse)
async def review_page(
    request: Request,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=10, le=200),
    status_filter: str = Query(default="pending", alias="status"),
    domain: str = Query(default="all"),
    q: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    """
    Paginated reviewer dashboard showing sentences filtered by validation status and domain.
    """
    query = db.query(Sentence).filter(Sentence.is_duplicate == False)

    if status_filter != "all":
        query = query.filter(Sentence.status == status_filter)

    if domain != "all":
        query = query.filter(Sentence.domain == domain)

    if q and q.strip():
        search_term = f"%{q.strip()}%"
        query = query.filter(
            Sentence.normalized_text.ilike(search_term) | Sentence.raw_text.ilike(search_term)
        )

    total = query.count()
    total_pages = max(1, (total + per_page - 1) // per_page)
    offset = (page - 1) * per_page
    sentences = query.order_by(Sentence.created_at.desc()).offset(offset).limit(per_page).all()

    # Calculate status counts for quick-filter tabs
    counts = {
        "all": db.query(Sentence).filter(Sentence.is_duplicate == False).count(),
        "pending": db.query(Sentence).filter(Sentence.is_duplicate == False, Sentence.status == "pending").count(),
        "approved": db.query(Sentence).filter(Sentence.is_duplicate == False, Sentence.status == "approved").count(),
        "flagged": db.query(Sentence).filter(Sentence.is_duplicate == False, Sentence.status == "flagged").count(),
        "rejected": db.query(Sentence).filter(Sentence.is_duplicate == False, Sentence.status == "rejected").count(),
    }

    # Available domains for dropdown filter
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
        name="review.html",
        context={
            "sentences": sentences,
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "status_filter": status_filter,
            "domain_filter": domain,
            "domains": sorted(domains),
            "search_query": q or "",
            "counts": counts,
            "user": user,
        },
    )


@router.post("/review/{sentence_id}/approve")
async def approve_sentence(
    sentence_id: str,
    return_url: str = Form(default="/review"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    """Approve a sentence for inclusion in the final training dataset."""
    sentence = db.query(Sentence).filter(Sentence.id == sentence_id).first()
    if sentence:
        sentence.status = "approved"
        sentence.reviewed_by = user.id if user else None
        sentence.reviewed_at = datetime.utcnow()
        db.commit()
    return RedirectResponse(url=return_url, status_code=status.HTTP_303_SEE_OTHER)


@router.post("/review/{sentence_id}/flag")
async def flag_sentence(
    sentence_id: str,
    note: str = Form(default=""),
    return_url: str = Form(default="/review"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    """Flag a sentence for linguistic anomalies, OCR noise, or orthographic defects."""
    sentence = db.query(Sentence).filter(Sentence.id == sentence_id).first()
    if sentence:
        sentence.status = "flagged"
        sentence.reviewer_note = note.strip()
        sentence.reviewed_by = user.id if user else None
        sentence.reviewed_at = datetime.utcnow()
        db.commit()
    return RedirectResponse(url=return_url, status_code=status.HTTP_303_SEE_OTHER)


@router.post("/review/{sentence_id}/edit")
async def edit_sentence(
    sentence_id: str,
    normalized_text: str = Form(...),
    return_url: str = Form(default="/review"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    """
    Allow a reviewer to manually correct orthographic errors in normalized text.
    Preserves raw_text for provenance tracking and marks the sentence as approved.
    """
    sentence = db.query(Sentence).filter(Sentence.id == sentence_id).first()
    if sentence and normalized_text.strip():
        clean_text = normalized_text.strip()
        sentence.normalized_text = clean_text
        sentence.char_count = len(clean_text)
        sentence.word_count = len(clean_text.split())
        sentence.status = "approved"
        sentence.reviewed_by = user.id if user else None
        sentence.reviewed_at = datetime.utcnow()
        db.commit()
    return RedirectResponse(url=return_url, status_code=status.HTTP_303_SEE_OTHER)


@router.post("/review/{sentence_id}/reject")
async def reject_sentence(
    sentence_id: str,
    return_url: str = Form(default="/review"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    """Mark a sentence as rejected (excluded from training)."""
    sentence = db.query(Sentence).filter(Sentence.id == sentence_id).first()
    if sentence:
        sentence.status = "rejected"
        sentence.reviewed_by = user.id if user else None
        sentence.reviewed_at = datetime.utcnow()
        db.commit()
    return RedirectResponse(url=return_url, status_code=status.HTTP_303_SEE_OTHER)
