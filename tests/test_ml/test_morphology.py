"""
Unit and Integration Tests for Awingi Morphology Subsystem
"""

import pytest
from src.ml.morphology.affix_tables import (
    CASE_SUFFIXES,
    VERBAL_PREFIXES,
    ALL_SUFFIXES_ORDERED,
)
from src.ml.morphology.evaluator import (
    evaluate_morphological_segmentation,
    get_boundary_indices,
)
from src.ml.morphology.segmenter import (
    AwingiMorphologicalSegmenter,
    Morpheme,
    WordSegmentation,
)


def test_affix_tables_integrity():
    """Verify linguistic affix tables contain essential Cushitic morphemes."""
    assert "tstsa" in CASE_SUFFIXES
    assert "da" in CASE_SUFFIXES
    assert "ma-" in VERBAL_PREFIXES
    assert ALL_SUFFIXES_ORDERED[0] == max(ALL_SUFFIXES_ORDERED, key=len)


def test_word_segmentation_case_suffixes():
    """Verify rule-guided suffix peeling on nominal case forms."""
    segmenter = AwingiMorphologicalSegmenter()

    seg1 = segmenter.segment_word("agawda")
    assert seg1.normalized_token == "agawda"
    assert seg1.stem.surface == "agaw"
    assert len(seg1.suffixes) == 1
    assert seg1.suffixes[0].surface == "da"
    assert seg1.suffixes[0].gloss == "LOC"
    assert seg1.segmented_string == "agaw-da"

    seg2 = segmenter.segment_word("awits")
    assert seg2.stem.surface == "awi"
    assert seg2.suffixes[0].surface == "ts"
    assert seg2.suffixes[0].gloss == "GEN"


def test_prefix_and_verbal_agreement():
    """Verify negative prefix and TAM agreement identification."""
    segmenter = AwingiMorphologicalSegmenter()

    seg = segmenter.segment_word("makɨda")
    assert seg.prefix is not None
    assert seg.prefix.surface == "ma"
    assert seg.prefix.gloss == "NEG"
    assert seg.stem.surface == "kɨd"
    assert len(seg.suffixes) >= 1
    assert seg.suffixes[-1].surface == "a"
    assert "ɨ" in seg.stem.surface


def test_special_characters_preservation():
    """Verify that Awingi-specific phonemes ɨ and ŋ are never stripped or altered."""
    segmenter = AwingiMorphologicalSegmenter()

    word = "ŋunada"
    seg = segmenter.segment_word(word)
    assert seg.stem.surface.startswith("ŋ")
    assert seg.segmented_string == "ŋuna-da"


def test_sentence_level_segmentation():
    """Verify whole-sentence decomposition and interlinear glossing."""
    segmenter = AwingiMorphologicalSegmenter()
    sentence = "Awi agawda qutɨrsɨ."
    words = segmenter.segment_sentence(sentence)

    assert len(words) == 3
    assert words[1].segmented_string == "agaw-da"
    assert words[1].gloss_string == "AGAW-LOC"


def test_morphology_evaluator():
    """Verify precision, recall, and F1 calculations on gold standard benchmarks."""
    segmenter = AwingiMorphologicalSegmenter()

    gold_pairs = [
        ("agawda", ["agaw", "da"]),
        ("awits", ["awi", "ts"]),
        ("makɨda", ["ma", "kɨd", "a"]),
    ]

    report = evaluate_morphological_segmentation(segmenter, gold_pairs)
    assert report.total_words == 3
    assert report.word_accuracy >= 0.6
    assert report.precision >= 0.8
    assert report.recall >= 0.8
    assert report.f1_score >= 0.8
