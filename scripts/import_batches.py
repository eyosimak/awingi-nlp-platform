#!/usr/bin/env python3
"""
Awingi NLP Platform — Batch Importer CLI Tool
Loads Computer 2's extracted JSON batch files into the local platform database.

Usage:
    python scripts/import_batches.py data/processed/
    python scripts/import_batches.py scripts/sample_data/sample_batch.json
"""

import argparse
import glob
import json
from pathlib import Path
import sys
import uuid

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.common.schemas import IngestionBatch
from src.platform.database import SessionLocal, init_db
from src.platform.models import Document, Sentence


def import_file(filepath: Path, db) -> int:
    """Import a single IngestionBatch JSON file into the database."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Validate strictly via shared Pydantic schema
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
    return added


def main():
    parser = argparse.ArgumentParser(description="Import IngestionBatch JSON files into database.")
    parser.add_argument(
        "target",
        nargs="?",
        default="data/processed",
        help="Path to JSON file or directory containing JSON files (default: data/processed)",
    )
    args = parser.parse_args()

    init_db()
    db = SessionLocal()

    target_path = Path(args.target)
    files = []

    if target_path.is_file() and target_path.suffix == ".json":
        files = [target_path]
    elif target_path.is_dir():
        files = sorted(target_path.glob("*.json"))
    else:
        # Try globbing directly
        files = [Path(p) for p in sorted(glob.glob(str(target_path)))]

    if not files:
        print(f"⚠️  No JSON batch files found matching: {args.target}")
        db.close()
        return

    print(f"📦 Found {len(files)} batch file(s) to import:")
    total_imported = 0

    for f in files:
        try:
            count = import_file(f, db)
            total_imported += count
            print(f"  ✓ {f.name}: {count} sentences imported")
        except Exception as e:
            print(f"  ❌ {f.name}: Error during import — {e}")

    db.close()
    print(f"\n🎉 Import complete! Successfully imported {total_imported} sentences across {len(files)} document(s).")


if __name__ == "__main__":
    main()
