"""
Awingi Document Ingestion CLI Runner
====================================
CLI entry point to discover documents, extract text, normalize Awingi
orthography, segment sentences, deduplicate across the corpus, and
export validated IngestionBatch JSON files.

Usage:
    python -m src.pipeline.run_ingest data/raw/ --output data/processed/ --sample 50
"""

import argparse
import json
from pathlib import Path
import random
import sys
from typing import Dict, List, Optional
from uuid import uuid4

# CRITICAL FOR WINDOWS CONSOLE UTF-8 SUPPORT
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from src.common.schemas import (
    CleanedSentence,
    DocumentType,
    ExtractedDocument,
    ExtractionStatus,
    IngestionBatch,
)
from src.pipeline.deduplicator import Deduplicator
from src.pipeline.extractors.base import BaseExtractor, ExtractionResult
from src.pipeline.extractors.docx_extractor import DOCXExtractor
from src.pipeline.extractors.pdf_extractor import PDFExtractor
from src.pipeline.extractors.txt_extractor import TXTExtractor
from src.pipeline.normalizer import detect_mixed_script, normalize_text
from src.pipeline.segmenter import segment_sentences


def get_extractors() -> Dict[str, BaseExtractor]:
    """
    Initialize and map all available file format extractors by extension.
    """
    extractors: List[BaseExtractor] = [
        PDFExtractor(),
        DOCXExtractor(),
        TXTExtractor(),
    ]
    ext_map: Dict[str, BaseExtractor] = {}
    for extractor in extractors:
        for ext in extractor.supported_extensions():
            ext_map[ext.lower()] = extractor
    return ext_map


def infer_doc_type(filename: str, fallback: DocumentType) -> DocumentType:
    """
    Infer DocumentType from filename keywords, defaulting to the fallback.
    """
    fn_lower = filename.lower()
    if "reader" in fn_lower or "primer" in fn_lower or "textbook" in fn_lower or "grade" in fn_lower:
        return DocumentType.TEXTBOOK
    if "agri" in fn_lower or "farm" in fn_lower or "crop" in fn_lower:
        return DocumentType.AGRICULTURE
    if "curric" in fn_lower or "syllabus" in fn_lower:
        return DocumentType.CURRICULUM
    if "dict" in fn_lower or "glossary" in fn_lower:
        return DocumentType.DICTIONARY
    if "relig" in fn_lower or "bible" in fn_lower or "church" in fn_lower:
        return DocumentType.RELIGIOUS
    if "lit" in fn_lower or "story" in fn_lower or "fiction" in fn_lower:
        return DocumentType.LITERATURE
    return fallback


def process_document(
    filepath: Path,
    extractor: BaseExtractor,
    deduplicator: Deduplicator,
    doc_type: Optional[DocumentType] = None,
    domain: str = "general",
    pipeline_version: str = "0.1.0",
) -> IngestionBatch:
    """
    Execute extraction, normalization, segmentation, and deduplication for a single document.
    """
    # 1. Extraction
    extraction: ExtractionResult = extractor.extract(str(filepath))

    status = ExtractionStatus.SUCCESS if extraction.success else ExtractionStatus.FAILED
    selected_doc_type = doc_type if doc_type is not None else infer_doc_type(filepath.name, DocumentType.OTHER)
    title = filepath.stem.replace("_", " ").replace("-", " ").title()

    doc_metadata = ExtractedDocument(
        source_filename=filepath.name,
        doc_type=selected_doc_type,
        title=title,
        total_characters=extraction.total_characters,
        total_raw_lines=extraction.total_lines,
        extraction_status=status,
        error_log=extraction.error_message if not extraction.success else None,
    )

    if not extraction.success:
        return IngestionBatch(
            document=doc_metadata,
            sentences=[],
            pipeline_version=pipeline_version,
        )

    # 2. Segmentation & Normalization
    raw_sentences = segment_sentences(extraction.raw_text)
    cleaned_sentences: List[CleanedSentence] = []

    for raw_s in raw_sentences:
        norm_s = normalize_text(raw_s)
        if not norm_s:
            continue

        # 3. Deduplication
        cleaned_sent = deduplicator.process_sentence(
            raw_text=raw_s,
            normalized_text=norm_s,
            domain=domain,
        )
        cleaned_sentences.append(cleaned_sent)

    return IngestionBatch(
        document=doc_metadata,
        sentences=cleaned_sentences,
        pipeline_version=pipeline_version,
    )


def print_spot_check_samples(sentences: List[CleanedSentence], count: int) -> None:
    """
    Print random sample sentences for native speaker linguistic review.
    """
    if not sentences:
        print("\nNo sentences available for spot-checking.")
        return

    sample_size = min(count, len(sentences))
    sampled = random.sample(sentences, sample_size)

    header = f"=== AWINGI LINGUISTIC SPOT-CHECK SAMPLES ({sample_size} sentences) ==="
    print("\n" + "=" * len(header))
    print(header)
    print("=" * len(header))

    for idx, s in enumerate(sampled, 1):
        dup_tag = f" [DUPLICATE of {s.duplicate_of_id[:8]}...]" if s.is_duplicate else ""
        has_special = any(c in s.normalized_text for c in ["ɨ", "Ɨ", "ŋ", "Ŋ", "'"])
        special_tag = " [SPECIAL_CHARS]" if has_special else ""
        print(f"[{idx:02d}] {s.normalized_text}{dup_tag}{special_tag}")
        print(f"     Words: {s.word_count:<3} | Chars: {s.char_count:<3} | Domain: {s.domain}")

    print("=" * len(header) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Awingi Document Ingestion & Data Preprocessing Pipeline"
    )
    parser.add_argument(
        "input_path",
        type=str,
        help="Path to input directory containing documents, or a single document file",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="data/processed",
        help="Target directory for processed IngestionBatch JSON files (default: data/processed)",
    )
    parser.add_argument(
        "--sample",
        "-s",
        type=int,
        default=0,
        help="Number of random sample sentences to display for linguistic spot-checking",
    )
    parser.add_argument(
        "--doc-type",
        type=str,
        default=None,
        choices=[t.value for t in DocumentType],
        help="Explicit document category override (e.g. textbook, agriculture, curriculum)",
    )
    parser.add_argument(
        "--domain",
        type=str,
        default="general",
        help="Domain classification for sentences (default: general)",
    )
    parser.add_argument(
        "--pipeline-version",
        type=str,
        default="0.1.0",
        help="Pipeline version identifier (default: 0.1.0)",
    )

    args = parser.parse_args()

    input_path = Path(args.input_path)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    ext_map = get_extractors()
    deduplicator = Deduplicator()

    # Discover candidate files
    target_files: List[Path] = []
    if input_path.is_file():
        target_files.append(input_path)
    elif input_path.is_dir():
        for ext in ext_map.keys():
            target_files.extend(input_path.rglob(f"*{ext}"))
    else:
        print(f"Error: Path '{input_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    # Sort files deterministically
    target_files.sort()

    if not target_files:
        print(f"No supported files found in '{input_path}'.")
        print(f"Supported extensions: {list(ext_map.keys())}")
        sys.exit(0)

    print(f"Discovered {len(target_files)} document(s) for ingestion.")
    all_sentences: List[CleanedSentence] = []
    override_type = DocumentType(args.doc_type) if args.doc_type else None

    for filepath in target_files:
        ext = filepath.suffix.lower()
        if ext not in ext_map:
            continue

        extractor = ext_map[ext]
        print(f"Processing: {filepath.name} ({extractor.__class__.__name__})...")

        batch = process_document(
            filepath=filepath,
            extractor=extractor,
            deduplicator=deduplicator,
            doc_type=override_type,
            domain=args.domain,
            pipeline_version=args.pipeline_version,
        )

        out_path = output_dir / f"{filepath.stem}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(batch.model_dump_json(indent=2))

        print(
            f"  -> Saved {out_path.name} "
            f"({len(batch.sentences)} sentences, status: {batch.document.extraction_status.value})"
        )
        all_sentences.extend(batch.sentences)

    print(f"\nIngestion complete. Total sentences processed across batch: {len(all_sentences)}")

    if args.sample > 0 and all_sentences:
        print_spot_check_samples(all_sentences, args.sample)


if __name__ == "__main__":
    main()
