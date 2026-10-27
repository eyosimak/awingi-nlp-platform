"""
Awingi Sentence Segmenter
=========================
Splits extracted document text into sentence units using regex lookbehind
on sentence boundaries (. ! ?), filtering out short fragments, isolated numbers,
and punctuation artifacts.
"""

import re
from typing import List


# Regex pattern splitting on whitespace immediately following sentence terminators
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")


def segment_sentences(text: str) -> List[str]:
    """
    Split text into valid sentence units.

    Rules:
      1. Splits across line boundaries and on sentence terminators (. ! ?)
      2. Discards empty strings and fragments without alphabetic characters
      3. Requires at least 2 words per sentence
      4. Strips leading and trailing whitespace

    Args:
        text: Raw or multi-line document text string.

    Returns:
        List of segmented sentence strings.
    """
    if not text:
        return []

    candidates: List[str] = []

    # First split across line breaks
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Split on sentence boundaries within the line
        parts = SENTENCE_SPLIT_PATTERN.split(line)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            candidates.append(part)

    valid_sentences: List[str] = []
    for candidate in candidates:
        # Rule: Must contain at least one alphabetic letter (filters pure numbers/symbols)
        if not any(ch.isalpha() for ch in candidate):
            continue

        # Rule: Must contain at least 2 words
        words = candidate.split()
        if len(words) < 2:
            continue

        valid_sentences.append(candidate)

    return valid_sentences
