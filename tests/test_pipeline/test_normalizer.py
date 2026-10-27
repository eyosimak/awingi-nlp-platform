"""
Unit Tests for Awingi Text Normalizer
=====================================
Validates orthography preservation (ɨ, Ɨ, ŋ, Ŋ, '), whitespace collapsing,
smart quote conversion, and mixed script detection.
"""

from src.pipeline.normalizer import detect_mixed_script, normalize_text


def test_awingi_special_characters_preservation():
    """Verify that barred-i and eng (both cases) and glottal stop are never stripped."""
    text = "Awi agawxi qutɨrsɨ Ɨŋka Ŋasɨ 'awan."
    normalized = normalize_text(text)
    assert "ɨ" in normalized, "Lowercase barred-i (ɨ) must be preserved"
    assert "Ɨ" in normalized, "Uppercase barred-i (Ɨ) must be preserved"
    assert "ŋ" in normalized, "Lowercase eng (ŋ) must be preserved"
    assert "Ŋ" in normalized, "Uppercase eng (Ŋ) must be preserved"
    assert "'" in normalized, "Glottal stop / apostrophe (') must be preserved"


def test_whitespace_and_tabs_collapsing():
    """Verify multiple spaces, tabs, and leading/trailing whitespace are collapsed."""
    raw = "   Awi\tagawxi    qutɨrsɨ. \t  "
    normalized = normalize_text(raw)
    assert normalized == "Awi agawxi qutɨrsɨ."


def test_smart_quotes_replacement():
    """Verify smart quotes are replaced with standard ASCII quotes."""
    # Smart single quotes
    raw_single = "\u2018Awi agawxi\u2019"
    assert normalize_text(raw_single) == "'Awi agawxi'"

    # Smart double quotes
    raw_double = "\u201CAwi agawxi\u201D"
    assert normalize_text(raw_double) == '"Awi agawxi"'


def test_unicode_nfkc_normalization():
    """Verify Unicode NFKC normalization decomposes/recomposes cleanly without losing Awingi characters."""
    # Combined accents / compatibility forms
    raw = "Dɨnxɨwa\u00A0kɨda"  # non-breaking space \u00A0
    normalized = normalize_text(raw)
    assert normalized == "Dɨnxɨwa kɨda"


def test_detect_mixed_script_pure_latin():
    """Verify detection on pure Awingi Latin text."""
    text = "Awi agawxi qutɨrsɨ. Dɨnxɨwa kɨda agawxi. Anbaŋ bɨsta antɨrsɨ."
    stats = detect_mixed_script(text)
    assert stats["latin_ratio"] > 0.95
    assert stats["ethiopic_ratio"] == 0.0
    assert stats["is_mixed"] is False


def test_detect_mixed_script_pure_ethiopic():
    """Verify detection on pure Ethiopic / Amharic text."""
    text = "ይህ በአዊ ዞን የሚገኝ የግብርና መረጃ ነው።"
    stats = detect_mixed_script(text)
    assert stats["ethiopic_ratio"] > 0.95
    assert stats["latin_ratio"] == 0.0
    assert stats["is_mixed"] is False


def test_detect_mixed_script_mixed():
    """Verify detection on mixed Latin (Awingi) and Ethiopic (Amharic) text."""
    text = "Awi agawxi qutɨrsɨ. ይህ በአዊ ዞን የሚገኝ የግብርና መረጃ ነው።"
    stats = detect_mixed_script(text)
    assert stats["latin_ratio"] > 0.1
    assert stats["ethiopic_ratio"] > 0.1
    assert stats["is_mixed"] is True
