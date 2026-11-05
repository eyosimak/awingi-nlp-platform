"""
Awingi NLP Platform — Morphology Evaluation Suite
Evaluates morphological boundary precision, recall, F1, and exact word accuracy
against linguist-annotated reference gold benchmarks.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

from src.ml.morphology.segmenter import AwingiMorphologicalSegmenter, WordSegmentation


@dataclass
class MorphologyEvalReport:
    """Evaluation summary metrics for morphological segmentation."""

    total_words: int
    exact_match_words: int
    word_accuracy: float
    total_predicted_boundaries: int
    total_gold_boundaries: int
    true_positive_boundaries: int
    precision: float
    recall: float
    f1_score: float


def get_boundary_indices(morphemes: List[str]) -> set:
    """Computes internal boundary character indices within a concatenated word."""
    boundaries = set()
    cum_len = 0
    for m in morphemes[:-1]:
        cum_len += len(m)
        boundaries.add(cum_len)
    return boundaries


def evaluate_morphological_segmentation(
    segmenter: AwingiMorphologicalSegmenter,
    gold_data: List[Tuple[str, List[str]]],
) -> MorphologyEvalReport:
    """
    Evaluates segmenter predictions on a list of (word_token, [morpheme_list]) pairs.
    Computes boundary precision, recall, F1, and exact word match accuracy.
    """
    total_words = len(gold_data)
    exact_matches = 0
    total_pred_boundaries = 0
    total_gold_boundaries = 0
    tp_boundaries = 0

    for word, gold_morphemes in gold_data:
        seg = segmenter.segment_word(word)
        pred_morphemes = seg.morpheme_chain

        if pred_morphemes == gold_morphemes:
            exact_matches += 1

        pred_bounds = get_boundary_indices(pred_morphemes)
        gold_bounds = get_boundary_indices(gold_morphemes)

        total_pred_boundaries += len(pred_bounds)
        total_gold_boundaries += len(gold_bounds)
        tp_boundaries += len(pred_bounds.intersection(gold_bounds))

    prec = (
        round(tp_boundaries / total_pred_boundaries, 4)
        if total_pred_boundaries > 0
        else 1.0
    )
    rec = (
        round(tp_boundaries / total_gold_boundaries, 4)
        if total_gold_boundaries > 0
        else 1.0
    )
    f1 = (
        round(2 * (prec * rec) / (prec + rec), 4)
        if (prec + rec) > 0
        else 0.0
    )
    acc = round(exact_matches / total_words, 4) if total_words > 0 else 0.0

    return MorphologyEvalReport(
        total_words=total_words,
        exact_match_words=exact_matches,
        word_accuracy=acc,
        total_predicted_boundaries=total_pred_boundaries,
        total_gold_boundaries=total_gold_boundaries,
        true_positive_boundaries=tp_boundaries,
        precision=prec,
        recall=rec,
        f1_score=f1,
    )
