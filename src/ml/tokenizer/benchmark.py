"""
Awingi NLP Platform — Tokenizer Benchmarking and Fertility Evaluation
Evaluates token fertility, vocabulary efficiency, and subword compression rates
for Awingi (Awngi, ISO 639-3: awn) against baseline tokenization strategies.
"""

import argparse
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Union

# Defensive import of sentencepiece
try:
    import sentencepiece as spm
    SPM_AVAILABLE = True
except ImportError:
    spm = None
    SPM_AVAILABLE = False


@dataclass
class TokenizerBenchmarkResult:
    """Benchmark metrics for a tokenizer on an evaluation text corpus."""

    tokenizer_name: str
    total_words: int
    total_tokens: int
    total_characters: int
    fertility: float  # tokens per word (lower is better, ideally 1.2 - 1.8)
    char_to_token_ratio: float  # characters per token (higher is better)
    unk_count: int
    unk_rate: float  # unk tokens / total tokens
    sample_segmentations: List[Dict[str, Union[str, List[str]]]]


def calculate_fertility(total_tokens: int, total_words: int) -> float:
    """Computes token fertility: tokens per whitespace-separated word."""
    return round(total_tokens / total_words, 3) if total_words > 0 else 0.0


def benchmark_sentencepiece(
    model_path: str,
    test_sentences: List[str],
    name: str = "Awingi SentencePiece",
) -> TokenizerBenchmarkResult:
    """
    Evaluates a trained SentencePiece model on a set of test sentences.
    Computes fertility, unk rate, and inspects morpheme segmentation.
    """
    if not SPM_AVAILABLE:
        raise RuntimeError("sentencepiece is required to benchmark a SentencePiece model.")

    sp = spm.SentencePieceProcessor(model_file=model_path)

    total_words = 0
    total_tokens = 0
    total_chars = 0
    total_unks = 0
    sample_segmentations = []

    unk_id = sp.unk_id()

    for idx, sentence in enumerate(test_sentences):
        sentence = sentence.strip()
        if not sentence:
            continue

        words = sentence.split()
        word_count = len(words)
        total_words += word_count
        total_chars += len(sentence)

        pieces = sp.encode(sentence, out_type=str)
        token_ids = sp.encode(sentence, out_type=int)

        total_tokens += len(token_ids)
        unks = token_ids.count(unk_id)
        total_unks += unks

        # Save up to 5 representative sample segmentations
        if idx < 5:
            sample_segmentations.append({
                "sentence": sentence,
                "pieces": pieces,
                "token_count": len(pieces),
                "word_count": word_count,
                "sentence_fertility": round(len(pieces) / word_count, 2) if word_count else 0,
            })

    fertility = calculate_fertility(total_tokens, total_words)
    char_ratio = round(total_chars / total_tokens, 2) if total_tokens > 0 else 0.0
    unk_rate = round(total_unks / total_tokens, 4) if total_tokens > 0 else 0.0

    return TokenizerBenchmarkResult(
        tokenizer_name=name,
        total_words=total_words,
        total_tokens=total_tokens,
        total_characters=total_chars,
        fertility=fertility,
        char_to_token_ratio=char_ratio,
        unk_count=total_unks,
        unk_rate=unk_rate,
        sample_segmentations=sample_segmentations,
    )


def benchmark_baseline_character(
    test_sentences: List[str],
    name: str = "Character-Level Baseline",
) -> TokenizerBenchmarkResult:
    """Evaluates naive character-level tokenization baseline."""
    total_words = 0
    total_tokens = 0
    total_chars = 0

    for sentence in test_sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        words = sentence.split()
        total_words += len(words)
        total_chars += len(sentence)
        total_tokens += len(sentence.replace(" ", ""))

    fertility = calculate_fertility(total_tokens, total_words)
    char_ratio = round(total_chars / total_tokens, 2) if total_tokens > 0 else 0.0

    return TokenizerBenchmarkResult(
        tokenizer_name=name,
        total_words=total_words,
        total_tokens=total_tokens,
        total_characters=total_chars,
        fertility=fertility,
        char_to_token_ratio=char_ratio,
        unk_count=0,
        unk_rate=0.0,
        sample_segmentations=[],
    )


def benchmark_baseline_word(
    test_sentences: List[str],
    name: str = "Word-Level Baseline",
) -> TokenizerBenchmarkResult:
    """Evaluates naive whitespace word-level baseline."""
    total_words = 0
    total_chars = 0

    for sentence in test_sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        words = sentence.split()
        total_words += len(words)
        total_chars += len(sentence)

    return TokenizerBenchmarkResult(
        tokenizer_name=name,
        total_words=total_words,
        total_tokens=total_words,
        total_characters=total_chars,
        fertility=1.0,
        char_to_token_ratio=round(total_chars / total_words, 2) if total_words > 0 else 0.0,
        unk_count=0,
        unk_rate=0.0,
        sample_segmentations=[],
    )


def compare_tokenizers(
    results: List[TokenizerBenchmarkResult],
) -> str:
    """Formats a comparative markdown report of benchmark results."""
    lines = [
        "| Tokenizer | Total Tokens | Words | Fertility (tokens/word) | Chars/Token | UNK Rate |",
        "| :--- | :---: | :---: | :---: | :---: | :---: |",
    ]
    for r in results:
        lines.append(
            f"| **{r.tokenizer_name}** | {r.total_tokens:,} | {r.total_words:,} | "
            f"**{r.fertility:.2f}** | {r.char_to_token_ratio:.2f} | {r.unk_rate * 100:.2f}% |"
        )
    return "\n".join(lines)


def main():
    """CLI runner for evaluating tokenizer fertility."""
    parser = argparse.ArgumentParser(description="Benchmark Awingi subword tokenizer.")
    parser.add_argument("--model", type=str, required=True, help="Path to trained .model file.")
    parser.add_argument("--test-file", type=str, help="Path to evaluation text file.")
    args = parser.parse_args()

    sentences = []
    if args.test_file:
        with open(args.test_file, "r", encoding="utf-8") as f:
            sentences = [line.strip() for line in f if line.strip()]
    else:
        # Default representative Awingi test suite (Latin and Ge'ez dual orthography)
        sentences = [
            "Awi agawxi qutɨrsɨ kɨda ŋa.",
            "Deshta antɨ antɨki deshta aqwɨ.",
            "ጋቲውቲ ዴብቴርት እንጅባራ ዩኒቨርሲቲ ኮምፒውተር ሳይንስ።",
            "አዊ ብሔረሰብ አስተዳደር ዞን ውስጥ የሚነገር ማዕከላዊ ኩሻዊ ቋንቋ ነው።",
            "ɨ́mpunaŋuna awni kɨtɨma ts'ege.",
        ]

    sp_res = benchmark_sentencepiece(args.model, sentences)
    word_res = benchmark_baseline_word(sentences)
    char_res = benchmark_baseline_character(sentences)

    print("\n=== Awingi Tokenizer Benchmark Report ===")
    print(compare_tokenizers([word_res, sp_res, char_res]))
    print("\n--- Sample Subword Segmentations ---")
    for s in sp_res.sample_segmentations:
        print(f"Sentence:  {s['sentence']}")
        print(f"Subwords:  {s['pieces']} (fertility: {s['sentence_fertility']})\n")


if __name__ == "__main__":
    main()
