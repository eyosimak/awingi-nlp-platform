"""
PDF Document Extractor
======================
Extracts text from PDF documents using PyMuPDF (fitz).
Filters out standalone page numbers and empty lines.
"""

from pathlib import Path
from typing import List
import pymupdf as fitz

from src.pipeline.extractors.base import BaseExtractor, ExtractionResult


class PDFExtractor(BaseExtractor):
    """
    Extractor for PDF files via PyMuPDF.
    """

    def supported_extensions(self) -> List[str]:
        return [".pdf"]

    def extract(self, filepath: str) -> ExtractionResult:
        path = Path(filepath)
        filename = path.name

        try:
            doc = fitz.open(filepath)
            raw_lines: List[str] = []

            for page in doc:
                text = page.get_text("text")
                for line in text.splitlines():
                    cleaned_line = line.strip()
                    # Skip empty lines
                    if not cleaned_line:
                        continue
                    # Filter out standalone page numbers (pure digits <= 4 chars)
                    if cleaned_line.isdigit() and len(cleaned_line) <= 4:
                        continue
                    raw_lines.append(cleaned_line)

            raw_text = "\n".join(raw_lines)
            total_characters = sum(len(line) for line in raw_lines)
            total_lines = len(raw_lines)

            return ExtractionResult(
                filename=filename,
                raw_text=raw_text,
                raw_lines=raw_lines,
                total_characters=total_characters,
                total_lines=total_lines,
                success=True,
                error_message="",
            )
        except Exception as e:
            return ExtractionResult(
                filename=filename,
                raw_text="",
                raw_lines=[],
                total_characters=0,
                total_lines=0,
                success=False,
                error_message=str(e),
            )
