"""
Awingi NLP Platform — Rule-Guided Morphological Segmenter
Decomposes Awingi words into prefixes, base stems, and suffix chains,
providing linguistic morpheme tagging and glossing for downstream NLP tasks.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from src.ml.morphology.affix_tables import (
    ALL_SUFFIXES_ORDERED,
    CASE_SUFFIXES,
    ENCLITICS,
    NOMINAL_DERIVATIONAL,
    VERBAL_EXTENSIONS,
    VERBAL_PREFIXES,
    VERBAL_TAM_SUFFIXES,
)
from src.pipeline.normalizer import is_ethiopic_char, normalize_text


@dataclass
class Morpheme:
    """Represents a single analyzed morpheme unit."""

    surface: str
    morpheme_type: str  # "prefix", "stem", "suffix", "enclitic"
    category: str  # "case", "tam_agreement", "valency", "polarity", "root", etc.
    gloss: str  # "GEN", "PST.1SG", "NEG", "ROOT", etc.


@dataclass
class WordSegmentation:
    """Represents the complete morphological breakdown of a word token."""

    raw_token: str
    normalized_token: str
    prefix: Optional[Morpheme] = None
    stem: Morpheme = field(default_factory=lambda: Morpheme("", "stem", "root", "ROOT"))
    suffixes: List[Morpheme] = field(default_factory=list)
    enclitics: List[Morpheme] = field(default_factory=list)

    @property
    def morpheme_chain(self) -> List[str]:
        """Returns list of surface strings: [prefix, stem, suffix1, suffix2]."""
        pieces = []
        if self.prefix:
            pieces.append(self.prefix.surface)
        if self.stem.surface:
            pieces.append(self.stem.surface)
        pieces.extend(s.surface for s in self.suffixes)
        pieces.extend(e.surface for e in self.enclitics)
        return pieces

    @property
    def segmented_string(self) -> str:
        """Returns hyphen-delimited morphological representation (e.g., 'agaw-xi')."""
        return "-".join(self.morpheme_chain) if self.morpheme_chain else self.normalized_token

    @property
    def gloss_string(self) -> str:
        """Returns interlinear morphological gloss (e.g., 'agaw-GEN')."""
        glosses = []
        if self.prefix:
            glosses.append(self.prefix.gloss)
        if self.stem.surface:
            glosses.append(self.stem.surface.upper())
        glosses.extend(s.gloss for s in self.suffixes)
        glosses.extend(e.gloss for e in self.enclitics)
        return "-".join(glosses)


class AwingiMorphologicalSegmenter:
    """
    Morphological analyzer and segmenter for Awingi.
    Combines prefix stripping, suffix chain peeling, and root constraint checking.
    """

    MIN_STEM_LENGTH = 2

    def __init__(self, min_stem_length: int = 2):
        self.min_stem_length = min_stem_length

    def _lookup_suffix(self, suffix_str: str) -> Optional[Morpheme]:
        """Resolves suffix grammar attributes from linguistic affix dictionaries."""
        if suffix_str in CASE_SUFFIXES:
            info = CASE_SUFFIXES[suffix_str]
            return Morpheme(suffix_str, "suffix", info["category"], info["gloss"])
        if suffix_str in NOMINAL_DERIVATIONAL:
            info = NOMINAL_DERIVATIONAL[suffix_str]
            return Morpheme(suffix_str, "suffix", info["category"], info["gloss"])
        if suffix_str in VERBAL_TAM_SUFFIXES:
            info = VERBAL_TAM_SUFFIXES[suffix_str]
            return Morpheme(suffix_str, "suffix", info["category"], info["gloss"])
        if suffix_str in VERBAL_EXTENSIONS:
            info = VERBAL_EXTENSIONS[suffix_str]
            return Morpheme(suffix_str, "suffix", info["category"], info["gloss"])
        if suffix_str in ENCLITICS or f"-{suffix_str}" in ENCLITICS:
            info = ENCLITICS.get(suffix_str) or ENCLITICS.get(f"-{suffix_str}")
            return Morpheme(suffix_str, "enclitic", info["category"], info["gloss"])
        return None

    def segment_word(self, token: str) -> WordSegmentation:
        """
        Decomposes an individual word token into its constituent morphemes.
        Preserves special Awingi orthographic characters (ɨ, ŋ, ').
        """
        clean_token = normalize_text(token).strip()
        if not clean_token:
            return WordSegmentation(token, clean_token)

        # Non-alphanumeric or punctuation tokens
        if not any(c.isalpha() or c in "ɨƗŋŊ" for c in clean_token):
            return WordSegmentation(
                raw_token=token,
                normalized_token=clean_token,
                stem=Morpheme(clean_token, "punct", "punctuation", "PUNCT"),
            )

        working = clean_token.lower()
        extracted_prefix: Optional[Morpheme] = None
        extracted_suffixes: List[Morpheme] = []
        extracted_enclitics: List[Morpheme] = []

        # 1. Prefix Extraction (e.g. ma- / m-)
        is_verbal = False
        for pfx, pfx_info in VERBAL_PREFIXES.items():
            plain_pfx = pfx.rstrip("-")
            if working.startswith(plain_pfx) and len(working) - len(plain_pfx) >= self.min_stem_length:
                extracted_prefix = Morpheme(
                    surface=clean_token[: len(plain_pfx)],
                    morpheme_type="prefix",
                    category=pfx_info["category"],
                    gloss=pfx_info["gloss"],
                )
                working = working[len(plain_pfx) :]
                is_verbal = True
                break

        # 2. Suffix Peeling (Constrained multi-tier peeling)
        max_peels = 2
        peels = 0
        peeled_case = False

        while peels < max_peels:
            matched = False
            for sfx in ALL_SUFFIXES_ORDERED:
                # Once nominal case is stripped, noun root is reached
                if peeled_case:
                    break

                # If word has verbal prefix, skip nominal case suffixes
                if is_verbal and sfx in CASE_SUFFIXES:
                    continue

                # Short single-letter suffixes (like 'a' or 'e') require stem >= 3 chars
                min_len = 3 if len(sfx) == 1 else self.min_stem_length

                if working.endswith(sfx) and len(working) - len(sfx) >= min_len:
                    morph = self._lookup_suffix(sfx)
                    if morph:
                        if morph.morpheme_type == "enclitic":
                            extracted_enclitics.insert(0, morph)
                        else:
                            extracted_suffixes.insert(0, morph)
                            if morph.category == "case":
                                peeled_case = True
                        working = working[: -len(sfx)]
                        matched = True
                        peels += 1
                        break
            if not matched or peeled_case:
                break

        # Base stem
        stem_morpheme = Morpheme(
            surface=working,
            morpheme_type="stem",
            category="root",
            gloss="ROOT",
        )

        return WordSegmentation(
            raw_token=token,
            normalized_token=clean_token,
            prefix=extracted_prefix,
            stem=stem_morpheme,
            suffixes=extracted_suffixes,
            enclitics=extracted_enclitics,
        )

    def segment_sentence(self, sentence: str) -> List[WordSegmentation]:
        """Segments all words in an input sentence."""
        tokens = sentence.strip().split()
        return [self.segment_word(tok) for tok in tokens]
