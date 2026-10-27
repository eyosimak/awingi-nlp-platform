"""
Unit Tests for Awingi Sentence Segmenter
========================================
Validates boundary splitting on punctuation (. ! ?), multi-line text,
filtering of short fragments (< 2 words), and rejection of non-alphabetic artifacts.
"""

from src.pipeline.segmenter import segment_sentences


def test_segmenter_punctuation_boundaries():
    """Verify sentence splitting on periods, question marks, and exclamation marks."""
    text = "Awi agawxi qutɨrsɨ. Mɨn agawxi gwayta? Deski gwayta! Yɨna katsa."
    sentences = segment_sentences(text)
    assert len(sentences) == 4
    assert sentences[0] == "Awi agawxi qutɨrsɨ."
    assert sentences[1] == "Mɨn agawxi gwayta?"
    assert sentences[2] == "Deski gwayta!"
    assert sentences[3] == "Yɨna katsa."


def test_segmenter_multiline_text():
    """Verify sentences across multiple lines are segmented properly."""
    text = """
    Awi agawxi qutɨrsɨ.
    Dɨnxɨwa kɨda agawxi.
    Anbaŋ bɨsta antɨrsɨ.
    """
    sentences = segment_sentences(text)
    assert len(sentences) == 3
    assert sentences[0] == "Awi agawxi qutɨrsɨ."
    assert sentences[1] == "Dɨnxɨwa kɨda agawxi."
    assert sentences[2] == "Anbaŋ bɨsta antɨrsɨ."


def test_segmenter_short_fragments_filtered():
    """Verify single-word fragments are discarded (minimum 2 words required)."""
    text = "Awi. Awi agawxi qutɨrsɨ. Agawxi."
    sentences = segment_sentences(text)
    assert len(sentences) == 1
    assert sentences[0] == "Awi agawxi qutɨrsɨ."


def test_segmenter_non_alphabetic_artifacts_filtered():
    """Verify isolated numbers, symbols, and punctuation artifacts are excluded."""
    text = """
    12345
    ...
    ---
    Awi agawxi qutɨrsɨ.
    42
    Dɨnxɨwa kɨda agawxi.
    """
    sentences = segment_sentences(text)
    assert len(sentences) == 2
    assert sentences[0] == "Awi agawxi qutɨrsɨ."
    assert sentences[1] == "Dɨnxɨwa kɨda agawxi."


def test_segmenter_special_characters_intact():
    """Verify Awingi barred-i and eng remain intact in segmented output."""
    text = "Anbaŋ bɨsta antɨrsɨ. Dɨnxɨwa kɨda agawxi."
    sentences = segment_sentences(text)
    assert "ŋ" in sentences[0]
    assert "ɨ" in sentences[1]
