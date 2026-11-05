"""
Awingi NLP Platform — Morphological Affix Tables
Grammatical affix inventories and morpheme specifications for Awingi (Awngi, ISO 639-3: awn).
Based on Cushitic linguistic grammar: Hetzron (1969, 1976), Joswig (2006, 2010),
and Agaw Studies documentation.
"""

from typing import Dict, List, Set


# ==============================================================================
# 1. NOMINAL CASE & DERIVATIONAL AFFIXES
# ==============================================================================

# Nominal case suffixes (ordered by length descending to prioritize greedy matches)
CASE_SUFFIXES: Dict[str, Dict[str, str]] = {
    # Genitive (Possessive)
    "tstsa": {"category": "case", "function": "genitive_fem", "gloss": "GEN.F"},
    "tsu": {"category": "case", "function": "genitive_masc", "gloss": "GEN.M"},
    "ts": {"category": "case", "function": "genitive", "gloss": "GEN"},
    "z": {"category": "case", "function": "genitive_voiced", "gloss": "GEN"},
    # Dative / Purposive (for, to)
    "stsa": {"category": "case", "function": "dative_fem", "gloss": "DAT.F"},
    "sta": {"category": "case", "function": "dative_fem_alt", "gloss": "DAT.F"},
    "sa": {"category": "case", "function": "dative_alt", "gloss": "DAT"},
    "s": {"category": "case", "function": "dative", "gloss": "DAT"},
    # Locative (in, at, on)
    "da": {"category": "case", "function": "locative", "gloss": "LOC"},
    "ka": {"category": "case", "function": "locative_alt", "gloss": "LOC"},
    # Ablative (from)
    "kan": {"category": "case", "function": "ablative_long", "gloss": "ABL"},
    "k": {"category": "case", "function": "ablative", "gloss": "ABL"},
    # Comitative / Instrumental (with, by means of)
    "desh": {"category": "case", "function": "instrumental", "gloss": "INS"},
    "li": {"category": "case", "function": "comitative", "gloss": "COM"},
    # Accusative / Definite Focus
    "wa": {"category": "case", "function": "accusative", "gloss": "ACC"},
    # Comparative (than, as)
    "tunt": {"category": "case", "function": "comparative", "gloss": "COMP"},
}

# Number and Gender Derivational Suffixes
NOMINAL_DERIVATIONAL: Dict[str, Dict[str, str]] = {
    # Plural suffixes
    "kà": {"category": "number", "function": "plural", "gloss": "PL"},
    "ka": {"category": "number", "function": "plural_plain", "gloss": "PL"},
    "ts": {"category": "number", "function": "plural_ts", "gloss": "PL"},
    # Singulative / Unitizer
    "tá": {"category": "number", "function": "singulative", "gloss": "SG"},
    "ta": {"category": "number", "function": "singulative_plain", "gloss": "SG"},
    "tsa": {"category": "gender", "function": "feminine_marker", "gloss": "FEM"},
}


# ==============================================================================
# 2. VERBAL INFLECTIONAL & DERIVATIONAL AFFIXES
# ==============================================================================

# Verbal prefixes (Negation & Causative/Passive particles)
VERBAL_PREFIXES: Dict[str, Dict[str, str]] = {
    # Negative prefixes
    "ma-": {"category": "polarity", "function": "negative_imperfective", "gloss": "NEG"},
    "m-": {"category": "polarity", "function": "negative_contracted", "gloss": "NEG"},
    "an-": {"category": "polarity", "function": "negative_subjunctive", "gloss": "NEG.SBJV"},
}

# Verbal Subject Agreement & Tense-Aspect-Mood (TAM) Suffixes
VERBAL_TAM_SUFFIXES: Dict[str, Dict[str, str]] = {
    # Past / Perfective paradigm
    "xá": {"category": "tam_agreement", "function": "past_1sg", "gloss": "PST.1SG"},
    "tí": {"category": "tam_agreement", "function": "past_2sg_3sgf", "gloss": "PST.2SG/3SGF"},
    "té": {"category": "tam_agreement", "function": "past_2sg_alt", "gloss": "PST.2SG"},
    "é": {"category": "tam_agreement", "function": "past_3sgm", "gloss": "PST.3SGM"},
    "né": {"category": "tam_agreement", "function": "past_1pl", "gloss": "PST.1PL"},
    "ná": {"category": "tam_agreement", "function": "past_1pl_alt", "gloss": "PST.1PL"},
    "tán": {"category": "tam_agreement", "function": "past_2pl", "gloss": "PST.2PL"},
    "án": {"category": "tam_agreement", "function": "past_3pl", "gloss": "PST.3PL"},
    # Imperfective / Present paradigm
    "kɨda": {"category": "tam_agreement", "function": "imperfective_aux", "gloss": "IPFV"},
    "a": {"category": "tam_agreement", "function": "imperfective_base", "gloss": "IPFV"},
    "e": {"category": "tam_agreement", "function": "imperfective_3sg", "gloss": "IPFV.3SG"},
    # Negative verbal suffixes
    "la": {"category": "polarity", "function": "negative_suffix", "gloss": "NEG"},
    "lam": {"category": "polarity", "function": "negative_connegative", "gloss": "NEG"},
}

# Verbal Stem Extension Suffixes (Valency & Derivation)
VERBAL_EXTENSIONS: Dict[str, Dict[str, str]] = {
    "sis": {"category": "valency", "function": "double_causative", "gloss": "CAUS2"},
    "s": {"category": "valency", "function": "causative", "gloss": "CAUS"},
    "int": {"category": "valency", "function": "passive_reflexive", "gloss": "PASS"},
    "t": {"category": "valency", "function": "passive_middle", "gloss": "PASS"},
    "ts": {"category": "valency", "function": "reciprocal", "gloss": "RECP"},
}


# ==============================================================================
# 3. CONJUNCTIONS & ENCLITICS
# ==============================================================================

ENCLITICS: Dict[str, Dict[str, str]] = {
    "-ki": {"category": "enclitic", "function": "conjunction_and", "gloss": "CONJ"},
    "ki": {"category": "enclitic", "function": "conjunction_and_unhyphenated", "gloss": "CONJ"},
    "-ma": {"category": "enclitic", "function": "focus_marker", "gloss": "FOC"},
    "ma": {"category": "enclitic", "function": "focus_marker_unhyphenated", "gloss": "FOC"},
    "ŋa": {"category": "particle", "function": "declarative_assertion", "gloss": "DECL"},
}


# Precomputed ordered lists for suffix stripping / greedy decomposition
ALL_SUFFIXES_ORDERED: List[str] = sorted(
    list(CASE_SUFFIXES.keys())
    + list(NOMINAL_DERIVATIONAL.keys())
    + list(VERBAL_TAM_SUFFIXES.keys())
    + list(VERBAL_EXTENSIONS.keys())
    + [e.lstrip("-") for e in ENCLITICS.keys()],
    key=lambda s: len(s),
    reverse=True,
)
