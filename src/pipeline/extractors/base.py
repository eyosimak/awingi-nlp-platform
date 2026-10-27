"""
Base Extractor Interface and Result Data Container
===================================================
Defines the abstract interface for all document extractors and the
ExtractionResult dataclass container.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List


@dataclass
class ExtractionResult:
    """
    Standardized result emitted by any document extractor.
    """
    filename: str
    raw_text: str
    raw_lines: List[str]
    total_characters: int
    total_lines: int
    success: bool
    error_message: str = ""


class BaseExtractor(ABC):
    """
    Abstract base class for all file format extractors (PDF, DOCX, TXT).
    """

    @abstractmethod
    def extract(self, filepath: str) -> ExtractionResult:
        """
        Extract raw text content from the specified file.

        Args:
            filepath: Path to the target document.

        Returns:
            ExtractionResult containing raw text, lines, statistics, and status.
        """
        pass

    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """
        List of supported lowercase file extensions (e.g., ['.pdf']).
        """
        pass
