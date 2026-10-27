"""
Awingi NLP Platform — Main Corpus Statistics Dashboard
Visualizes corpus collection scale, validation progress, and linguistic domains.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session
from src.platform.database import get_db
from src.platform.models import Document, Sentence
from src.platform.auth.dependencies import get_current_user_optional

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="src/platform/templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    """
    Renders the platform overview dashboard showing real-time corpus statistics.
    """
    total_docs = db.query(Document).count()
    total_sents = db.query(Sentence).filter(Sentence.is_duplicate == False).count()
    approved_sents = db.query(Sentence).filter(
        Sentence.is_duplicate == False, Sentence.status == "approved"
    ).count()
    pending_sents = db.query(Sentence).filter(
        Sentence.is_duplicate == False, Sentence.status == "pending"
    ).count()
    flagged_sents = db.query(Sentence).filter(
        Sentence.is_duplicate == False, Sentence.status == "flagged"
    ).count()
    rejected_sents = db.query(Sentence).filter(
        Sentence.is_duplicate == False, Sentence.status == "rejected"
    ).count()
    duplicate_sents = db.query(Sentence).filter(Sentence.is_duplicate == True).count()

    total_words = (
        db.query(func.sum(Sentence.word_count))
        .filter(Sentence.is_duplicate == False)
        .scalar()
        or 0
    )

    approval_rate = (
        round((approved_sents / total_sents) * 100, 1) if total_sents > 0 else 0.0
    )

    domain_counts = (
        db.query(Sentence.domain, func.count(Sentence.id))
        .filter(Sentence.is_duplicate == False)
        .group_by(Sentence.domain)
        .all()
    )

    recent_documents = (
        db.query(Document).order_by(Document.created_at.desc()).limit(8).all()
    )

    stats = {
        "total_documents": total_docs,
        "total_sentences": total_sents,
        "approved_sentences": approved_sents,
        "pending_sentences": pending_sents,
        "flagged_sentences": flagged_sents,
        "rejected_sentences": rejected_sents,
        "duplicate_sentences": duplicate_sents,
        "total_words": int(total_words),
        "approval_rate": approval_rate,
        "domains": [{"domain": d[0], "count": d[1]} for d in domain_counts],
        "recent_documents": recent_documents,
    }

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "stats": stats,
            "user": user,
        },
    )
