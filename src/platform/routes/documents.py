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

    # Bulk query sentence status counts in a single query
    counts_query = (
        db.query(
            Sentence.document_id,
            Sentence.status,
            func.count(Sentence.id),
        )
        .group_by(Sentence.document_id, Sentence.status)
        .all()
    )

    stats_map = {}
    for doc_id, stat_name, cnt in counts_query:
        if doc_id not in stats_map:
            stats_map[doc_id] = {
                "total": 0,
                "approved": 0,
                "pending": 0,
                "flagged": 0,
                "rejected": 0,
            }
        stats_map[doc_id]["total"] += cnt
        if stat_name in stats_map[doc_id]:
            stats_map[doc_id][stat_name] = cnt

    doc_stats = []
    for doc in documents:
        s = stats_map.get(
            doc.id,
            {"total": 0, "approved": 0, "pending": 0, "flagged": 0, "rejected": 0},
        )
        total = s["total"]
        approved = s["approved"]
        doc_stats.append({
            "doc": doc,
            "total": total,
            "approved": approved,
            "pending": s["pending"],
            "flagged": s["flagged"],
            "rejected": s["rejected"],
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
    Delete a document and all associated sentences via fast bulk deletion.
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    filename = doc.source_filename
    db.query(Sentence).filter(Sentence.document_id == doc_id).delete(synchronize_session=False)
    db.query(Document).filter(Document.id == doc_id).delete(synchronize_session=False)
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
    Finds documents with identical source_filename.
    Keeps the one with the most approved sentences (or earliest created),
    and fast-bulk-deletes duplicate document runs.
    """
    documents = db.query(Document).order_by(Document.created_at.asc()).all()

    # Pre-fetch approved sentence counts per document in one aggregation query
    approved_counts = dict(
        db.query(Sentence.document_id, func.count(Sentence.id))
        .filter(Sentence.status == "approved")
        .group_by(Sentence.document_id)
        .all()
    )

    # Group by source_filename
    grouped = {}
    for doc in documents:
        grouped.setdefault(doc.source_filename, []).append(doc)

    all_dup_ids = []
    cleaned_names = []

    for filename, doc_list in grouped.items():
        if len(doc_list) > 1:
            def doc_score(d):
                app_count = approved_counts.get(d.id, 0)
                created_ts = d.created_at.timestamp() if d.created_at else 0.0
                return (app_count, -created_ts)

            doc_list.sort(key=doc_score, reverse=True)
            duplicates = doc_list[1:]
            for dup in duplicates:
                all_dup_ids.append(dup.id)
            cleaned_names.append(filename)

    deleted_count = len(all_dup_ids)
    if all_dup_ids:
        # Fast bulk cascade deletion
        db.query(Sentence).filter(Sentence.document_id.in_(all_dup_ids)).delete(synchronize_session=False)
        db.query(Document).filter(Document.id.in_(all_dup_ids)).delete(synchronize_session=False)
        db.commit()

    if deleted_count > 0:
        msg = f"Cleaned+up+{deleted_count}+duplicate+document+runs+across+{len(cleaned_names)}+source+files."
    else:
        msg = "No+duplicate+documents+were+found."

    return RedirectResponse(
        url=f"/documents?message={msg}",
        status_code=status.HTTP_303_SEE_OTHER,
    )
