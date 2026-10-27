"""
Awingi Orthography-Preserving Text Normalizer
============================================
Handles Unicode NFKC normalization, whitespace collapsing, smart quote
standardization, script detection, and strict preservation of Awingi
special characters:
  - ɨ (U+0268) / Ɨ (U+0197) [barred-i]
  - ŋ (U+014B) / Ŋ (U+014A) [eng]
  - ' (U+0027) [glottal stop / apostrophe]
"""

import re
import unicodedata
from typing import Any, Dict


ETHIOPIC_RANGES = [
    (0x1200, 0x137F),  # Ethiopic
    (0x1380, 0x139F),  # Ethiopic Supplement
    (0x2D80, 0x2DDF),  # Ethiopic Extended
    (0xAB00, 0xAB2F),  # Ethiopic Extended-A
]


def is_ethiopic_char(char: str) -> bool:
    """Check if character falls into Ethiopic/Ge'ez Unicode blocks."""
    cp = ord(char)
    return any(start <= cp <= end for start, end in ETHIOPIC_RANGES)


def is_latin_char(char: str) -> bool:
    """Check if character is Latin (including Awingi special Latin extensions)."""
    if not char.isalpha():
        return False
    cp = ord(char)
    # ASCII Latin, Latin-1 Supplement, Latin Extended-A & B, IPA Extensions
    if (0x0041 <= cp <= 0x005A) or (0x0061 <= cp <= 0x007A) or (0x00C0 <= cp <= 0x02AF):
        return True
    try:
        return unicodedata.name(char, "").startswith("LATIN")
    except ValueError:
        return False


def normalize_text(text: str) -> str:
    """
    Normalize text preserving Awingi orthography.

    Steps:
      1. Apply unicodedata.normalize('NFKC', text)
      2. Replace smart single quotes (\\u2018, \\u2019) with standard ASCII apostrophe (')
      3. Replace smart double quotes (\\u201C, \\u201D) with standard ASCII double quote (\")
      4. Collapse excessive spaces and tabs into a single space
      5. Strip leading and trailing whitespace
      6. Explicitly preserve Awingi special characters: ɨ, Ɨ, ŋ, Ŋ, and '

    Args:
        text: Raw input text.

    Returns:
        Cleaned, normalized text string.
    """
    if not text:
        return ""

    # 1. Unicode NFKC normalization
    normalized = unicodedata.normalize("NFKC", text)

    # 2. Replace smart single quotes
    normalized = normalized.replace("\u2018", "'").replace("\u2019", "'")
    # Also handle alternate curly single quotes
    normalized = normalized.replace("\u201A", "'").replace("\u201B", "'")

    # 3. Replace smart double quotes
    normalized = normalized.replace("\u201C", '"').replace("\u201D", '"')
    # Also handle alternate curly double quotes
    normalized = normalized.replace("\u201E", '"').replace("\u201F", '"')

    # 4. Collapse excessive spaces and horizontal tabs
    normalized = re.sub(r"[ \t]+", " ", normalized)

    # 5. Strip leading/trailing whitespace
    normalized = normalized.strip()

    return normalized


def detect_mixed_script(text: str) -> Dict[str, Any]:
    """
    Analyze text to detect the proportion of Latin vs Ethiopic/Ge'ez script.
    Helps identify if a document has mixed Amharic/Awingi content.

    Args:
        text: Input text string.

    Returns:
        Dictionary with Latin and Ethiopic character counts, ratios,
        percentages, and a boolean `is_mixed` flag.
    """
    latin_count = 0
    ethiopic_count = 0
    total_alpha = 0

    for ch in text:
        if ch.isalpha():
            total_alpha += 1
            if is_latin_char(ch):
                latin_count += 1
            elif is_ethiopic_char(ch):
                ethiopic_count += 1

    if total_alpha == 0:
        return {
            "total_alpha": 0,
            "latin_count": 0,
            "ethiopic_count": 0,
            "latin_ratio": 0.0,
            "ethiopic_ratio": 0.0,
            "latin_pct": 0.0,
            "ethiopic_pct": 0.0,
            "is_mixed": False,
        }

    latin_ratio = round(latin_count / total_alpha, 4)
    ethiopic_ratio = round(ethiopic_count / total_alpha, 4)
    latin_pct = round(latin_ratio * 100, 2)
    ethiopic_pct = round(ethiopic_ratio * 100, 2)

    # Mixed if both scripts each account for at least 5% of alphabetic characters
    is_mixed = (latin_ratio >= 0.05) and (ethiopic_ratio >= 0.05)

    return {
        "total_alpha": total_alpha,
        "latin_count": latin_count,
        "ethiopic_count": ethiopic_count,
        "latin_ratio": latin_ratio,
        "ethiopic_ratio": ethiopic_ratio,
        "latin_pct": latin_pct,
        "ethiopic_pct": ethiopic_pct,
        "is_mixed": is_mixed,
    }
