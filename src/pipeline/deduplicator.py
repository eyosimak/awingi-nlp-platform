"""
Exact Sentence Deduplication Engine
===================================
Provides SHA-256 hash-based deduplication across documents and entire
ingestion runs, identifying duplicates and linking back to the first
occurrence identifier.
"""

import hashlib
from typing import Dict, Optional
from uuid import uuid4

from src.common.schemas import CleanedSentence


class Deduplicator:
    """
    Stateful deduplication engine maintaining seen hashes across documents.
    """

    def __init__(self):
        # Maps lowercase normalized text SHA-256 hash -> first occurrence identifier
        self.seen_hashes: Dict[str, str] = {}

    @staticmethod
    def compute_hash(text: str) -> str:
        """
        Compute SHA-256 digest of lowercase trimmed text.
        """
        clean_key = text.strip().lower()
        return hashlib.sha256(clean_key.encode("utf-8")).hexdigest()

    def process_sentence(
        self,
        raw_text: str,
        normalized_text: str,
        sentence_id: Optional[str] = None,
        document_id: Optional[str] = None,
        domain: str = "general",
        orthography_standard: str = "latin_official",
        language: str = "awn",
    ) -> CleanedSentence:
        """
        Process a sentence candidate against seen hashes and construct a CleanedSentence.

        Args:
            raw_text: Original uncleaned text line.
            normalized_text: Normalized Awingi text string.
            sentence_id: Optional unique identifier for this sentence.
            document_id: Optional ID of the parent document.
            domain: Semantic domain (general, agriculture, education, etc.).
            orthography_standard: Orthography variant (latin_official).
            language: ISO 639-3 language code ('awn').

        Returns:
            Validated CleanedSentence with deduplication metadata populated.
        """
        text_hash = self.compute_hash(normalized_text)
        is_duplicate = text_hash in self.seen_hashes

        if is_duplicate:
            duplicate_of_id = self.seen_hashes[text_hash]
        else:
            duplicate_of_id = None
            assigned_id = sentence_id if sentence_id is not None else text_hash
            self.seen_hashes[text_hash] = assigned_id

        words = normalized_text.split()
        char_count = len(normalized_text)
        word_count = len(words)

        return CleanedSentence(
            document_id=document_id,
            raw_text=raw_text,
            normalized_text=normalized_text,
            language=language,
            char_count=char_count,
            word_count=word_count,
            is_duplicate=is_duplicate,
            duplicate_of_id=duplicate_of_id,
            orthography_standard=orthography_standard,
            domain=domain,
        )

    def reset(self) -> None:
        """Clear all stored hashes."""
        self.seen_hashes.clear()
