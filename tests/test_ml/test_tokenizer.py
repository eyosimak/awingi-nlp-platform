"""
Unit and Integration Tests for Awingi Tokenizer Subsystem
"""

import os
import tempfile
import pytest

from src.ml.tokenizer.config import AWINGI_SPECIAL_SYMBOLS, ETHIOPIC_PUNCTUATION, TokenizerConfig
from src.ml.tokenizer.train_tokenizer import prepare_training_text, train_sentencepiece, SPM_AVAILABLE
from src.ml.tokenizer.benchmark import (
    calculate_fertility,
    benchmark_baseline_word,
    benchmark_baseline_character,
    benchmark_sentencepiece,
    compare_tokenizers,
)


SAMPLE_AWINGI_CORPUS = [
    "Awi agawxi qutɨrsɨ kɨda ŋa.",
    "Deshta antɨ antɨki deshta aqwɨ.",
    "Awingi luwatsa gitsishi tsetsetsa.",
    "Bɨra bɨrki ŋuna kɨtɨma ts'ege.",
    "ጋቲውቲ ዴብቴርት እንጅባራ ዩኒቨርሲቲ ኮምፒውተር ሳይንስ።",
    "አዊ ብሔረሰብ አስተዳደር ዞን ውስጥ የሚነገር ማዕከላዊ ኩሻዊ ቋንቋ ነው።",
]


def test_tokenizer_config_defaults():
    """Verify tokenizer config initializes with proper Awingi linguistic symbols."""
    config = TokenizerConfig(vocab_size=1000)
    assert config.vocab_size == 1000
    assert "ɨ" in config.user_defined_symbols
    assert "ŋ" in config.user_defined_symbols
    assert config.byte_fallback is True

    spm_args = config.to_spm_args(input_path="/tmp/test.txt", model_prefix="/tmp/m")
    assert "--input=/tmp/test.txt" in spm_args
    assert "--vocab_size=1000" in spm_args
    assert "--user_defined_symbols=" in spm_args
    assert "ɨ,Ɨ,ŋ,Ŋ,'" in spm_args


def test_prepare_training_text():
    """Verify training text preparation normalizes text and preserves barred-i and eng."""
    raw_inputs = [
        "Awi  agawxi    qutɨrsɨ  'kɨda'   ŋa!   ",
        "  ጋቲውቲ    ዴብቴርት  ።  ",
    ]
    temp_path = prepare_training_text(raw_inputs)
    try:
        assert os.path.exists(temp_path)
        with open(temp_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "qutɨrsɨ" in content
        assert "ŋa" in content
        assert "ጋቲውቲ" in content
        # Collapsed spaces
        assert "  " not in content
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_calculate_fertility_and_baselines():
    """Verify fertility calculation math and baseline benchmarks."""
    sentences = ["Awi agawxi qutɨrsɨ.", "Deshta aqwɨ."]
    word_res = benchmark_baseline_word(sentences)
    assert word_res.total_words == 5
    assert word_res.total_tokens == 5
    assert word_res.fertility == 1.0

    char_res = benchmark_baseline_character(sentences)
    assert char_res.total_words == 5
    assert char_res.total_tokens == len("Awiagawxiqutɨrsɨ.Deshtaaqwɨ.")
    assert char_res.fertility > 4.0

    report = compare_tokenizers([word_res, char_res])
    assert "| **Word-Level Baseline** |" in report
    assert "| **Character-Level Baseline** |" in report


@pytest.mark.skipif(not SPM_AVAILABLE, reason="sentencepiece binary not installed")
def test_train_and_benchmark_sentencepiece():
    """Verify end-to-end training, encoding, decoding, and benchmarking with SentencePiece."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Replicate small corpus to satisfy minimum vocab requirement
        repeated_corpus = SAMPLE_AWINGI_CORPUS * 20
        config = TokenizerConfig(vocab_size=100, model_type="bpe")

        result = train_sentencepiece(
            corpus=repeated_corpus,
            output_dir=tmpdir,
            model_prefix="test_awingi",
            config=config,
        )

        assert result["status"] == "success"
        assert os.path.exists(result["model_path"])
        assert os.path.exists(result["vocab_path"])
        assert result["vocab_size"] > 0
        assert result["sample_verification"]["lossless"] is True

        # Run benchmark on trained model
        bench = benchmark_sentencepiece(
            model_path=result["model_path"],
            test_sentences=SAMPLE_AWINGI_CORPUS,
        )
        assert bench.total_words > 0
        assert bench.fertility >= 1.0
        assert bench.fertility < 5.0
        assert bench.unk_rate == 0.0  # Byte fallback ensures 0 UNK rate
