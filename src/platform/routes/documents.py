"""
Awingi NLP Platform — Source Document Management
Allows researchers to view, inspect, audit, deduplicate, and prune source document batches.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
from src.platform.database import get_db
from src.platform.models import Document, Sentence
from src.platform.templates import templates
from src.platform.auth.dependencies import get_current_user_optional

router = APIRouter(tags=["documents"])


@router.get("/documents", response_class=HTMLResponse)
async def documents_page(
    request: Request,
    message: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    """
    Renders the document management catalog showing all ingested books, readers,
    and articles with per-document validation telemetry and deletion actions.
    """
    documents = db.query(Document).order_by(Document.created_at.desc()).all()

    doc_stats = []
    for doc in documents:
        total = db.query(Sentence).filter(Sentence.document_id == doc.id).count()
        approved = (
            db.query(Sentence)
            .filter(Sentence.document_id == doc.id, Sentence.status == "approved")
            .count()
        )
        pending = (
            db.query(Sentence)
            .filter(Sentence.document_id == doc.id, Sentence.status == "pending")
            .count()
        )
        flagged = (
            db.query(Sentence)
            .filter(Sentence.document_id == doc.id, Sentence.status == "flagged")
            .count()
        )
        rejected = (
            db.query(Sentence)
            .filter(Sentence.document_id == doc.id, Sentence.status == "rejected")
            .count()
        )

        doc_stats.append({
            "doc": doc,
            "total": total,
            "approved": approved,
            "pending": pending,
            "flagged": flagged,
            "rejected": rejected,
            "approval_rate": round((approved / total * 100), 1) if total > 0 else 0.0,
        })

    # Check for potential duplicates by filename
    filenames = [d.source_filename for d in documents]
    has_duplicate_filenames = len(filenames) != len(set(filenames))

    return templates.TemplateResponse(
        request=request,
        name="documents.html",
        context={
            "documents": doc_stats,
            "has_duplicate_filenames": has_duplicate_filenames,
            "message": message,
            "error": error,
            "user": user,
        },
    )


@router.post("/documents/{doc_id}/delete")
async def delete_document(
    doc_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    """
    Delete a document and all associated sentences via cascade deletion.
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    filename = doc.source_filename
    db.delete(doc)
    db.commit()

    return RedirectResponse(
        url=f"/documents?message=Document+{filename}+and+all+its+sentences+were+successfully+deleted.",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/documents/deduplicate")
async def deduplicate_documents(
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    """
    Finds documents with identical source_filename and total_sentences.
    Keeps the one with the most approved sentences (or earliest created),
    and deletes all duplicate document runs.
    """
    documents = db.query(Document).order_by(Document.created_at.asc()).all()

    # Group by source_filename
    grouped = {}
    for doc in documents:
        grouped.setdefault(doc.source_filename, []).append(doc)

    deleted_count = 0
    cleaned_names = []

    for filename, doc_list in grouped.items():
        if len(doc_list) > 1:
            # Score documents: prefer the one with highest approved count, then earliest created
            def doc_score(d):
                app_count = db.query(Sentence).filter(Sentence.document_id == d.id, Sentence.status == "approved").count()
                return (app_count, -d.created_at.timestamp())

            doc_list.sort(key=doc_score, reverse=True)
            keeper = doc_list[0]
            duplicates = doc_list[1:]

            for dup in duplicates:
                db.delete(dup)
                deleted_count += 1
            cleaned_names.append(filename)

    db.commit()

    if deleted_count > 0:
        msg = f"Cleaned+up+{deleted_count}+duplicate+document+runs+across+{len(cleaned_names)}+source+files."
    else:
        msg = "No+duplicate+documents+were+found."

    return RedirectResponse(
        url=f"/documents?message={msg}",
        status_code=status.HTTP_303_SEE_OTHER,
    )
