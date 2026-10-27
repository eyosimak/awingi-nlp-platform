"""
Awingi Document Ingestion & Data Preprocessing Pipeline
=======================================================
Computer 2 workspace package for extracting, normalizing, segmenting,
deduplicating, and serializing Awingi corpus data.
"""

from src.pipeline.deduplicator import Deduplicator
from src.pipeline.normalizer import detect_mixed_script, normalize_text
from src.pipeline.segmenter import segment_sentences

__all__ = [
    "Deduplicator",
    "normalize_text",
    "detect_mixed_script",
    "segment_sentences",
]
