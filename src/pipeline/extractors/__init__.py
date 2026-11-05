"""
Document Extractors Subsystem
"""

from src.pipeline.extractors.base import BaseExtractor, ExtractionResult
from src.pipeline.extractors.docx_extractor import DOCXExtractor
from src.pipeline.extractors.pdf_extractor import PDFExtractor
from src.pipeline.extractors.txt_extractor import TXTExtractor

__all__ = [
    "BaseExtractor",
    "ExtractionResult",
    "PDFExtractor",
    "DOCXExtractor",
    "TXTExtractor",
]
