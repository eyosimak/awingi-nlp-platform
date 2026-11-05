"""
Awingi NLP Platform — Morphological Analysis and Segmentation Subsystem
"""

from src.ml.morphology.affix_tables import (
    CASE_SUFFIXES,
    NOMINAL_DERIVATIONAL,
    VERBAL_PREFIXES,
    VERBAL_TAM_SUFFIXES,
    VERBAL_EXTENSIONS,
    ENCLITICS,
)
from src.ml.morphology.segmenter import (
    AwingiMorphologicalSegmenter,
    Morpheme,
    WordSegmentation,
)
from src.ml.morphology.evaluator import (
    MorphologyEvalReport,
    evaluate_morphological_segmentation,
)

__all__ = [
    "CASE_SUFFIXES",
    "NOMINAL_DERIVATIONAL",
    "VERBAL_PREFIXES",
    "VERBAL_TAM_SUFFIXES",
    "VERBAL_EXTENSIONS",
    "ENCLITICS",
    "AwingiMorphologicalSegmenter",
    "Morpheme",
    "WordSegmentation",
    "MorphologyEvalReport",
    "evaluate_morphological_segmentation",
]
