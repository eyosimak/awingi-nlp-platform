"""
TXT Document Extractor
======================
Extracts text from plain text (.txt) files using multi-encoding fallback.
"""

from pathlib import Path
from typing import List

from src.pipeline.extractors.base import BaseExtractor, ExtractionResult


class TXTExtractor(BaseExtractor):
    """
    Extractor for plain text (.txt) documents.
    Attempts multiple encodings: utf-8, utf-8-sig, cp1252, latin-1.
    """

    ENCODINGS = ["utf-8", "utf-8-sig", "cp1252", "latin-1"]

    def supported_extensions(self) -> List[str]:
        return [".txt"]

    def extract(self, filepath: str) -> ExtractionResult:
        path = Path(filepath)
        filename = path.name
        content = None
        last_error = ""

        for encoding in self.ENCODINGS:
            try:
                with open(filepath, "r", encoding=encoding) as f:
                    content = f.read()
                    break
            except UnicodeDecodeError as e:
                last_error = str(e)
                continue
            except Exception as e:
                last_error = str(e)
                break

        if content is None:
            return ExtractionResult(
                filename=filename,
                raw_text="",
                raw_lines=[],
                total_characters=0,
                total_lines=0,
                success=False,
                error_message=f"Failed to read file with any supported encoding: {last_error}",
            )

        raw_lines = [line.strip() for line in content.splitlines() if line.strip()]
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
