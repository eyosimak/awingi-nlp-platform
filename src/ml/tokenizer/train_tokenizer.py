"""
Awingi NLP Platform — SentencePiece Tokenizer Training Harness
Trains subword tokenizers (BPE or Unigram) specifically optimized for
Awingi (Awngi, ISO 639-3: awn) Latin and Ethiopic dual orthographies.
"""

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import List, Optional, Union

from src.ml.tokenizer.config import AWINGI_SPECIAL_SYMBOLS, TokenizerConfig
from src.pipeline.normalizer import normalize_text

# Defensive import of sentencepiece
try:
    import sentencepiece as spm
    SPM_AVAILABLE = True
except ImportError:
    spm = None
    SPM_AVAILABLE = False


def prepare_training_text(
    input_source: Union[str, Path, List[str]],
) -> str:
    """
    Extracts, normalizes, strips item number prefixes, and serializes training corpus lines
    into a temporary file ready for SentencePiece training.
    Supports plaintext files, JSONL export files, and Python lists.
    """
    lines = []
    if isinstance(input_source, (str, Path)) and os.path.exists(str(input_source)):
        with open(input_source, "r", encoding="utf-8") as f:
            for raw_line in f:
                line_str = raw_line.strip()
                if not line_str:
                    continue
                if line_str.startswith("{") and line_str.endswith("}"):
                    try:
                        data = json.loads(line_str)
                        line_str = data.get("text") or data.get("raw_text") or ""
                    except Exception:
                        pass
                clean = normalize_text(line_str)
                # Strip leading enumeration item numbers (e.g. '257,')
                clean = re.sub(r"^\d+[,.\-]\s*", "", clean).strip()
                if clean:
                    lines.append(clean)
    elif isinstance(input_source, list):
        for raw_line in input_source:
            clean = normalize_text(raw_line)
            clean = re.sub(r"^\d+[,.\-]\s*", "", clean).strip()
            if clean:
                lines.append(clean)
    else:
        raise ValueError(f"Invalid input_source provided: {input_source}")

    if not lines:
        raise ValueError("Corpus has no valid non-empty normalized sentences for training.")

    temp_file = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        delete=False,
        suffix="_awingi_spm_train.txt",
    )
    for line in lines:
        temp_file.write(f"{line}\n")
    temp_file.close()

    return temp_file.name


def train_sentencepiece(
    corpus: Union[str, Path, List[str]],
    output_dir: Union[str, Path] = "models/tokenizer",
    model_prefix: str = "awingi_spm",
    config: Optional[TokenizerConfig] = None,
) -> dict:
    """
    Executes SentencePiece training using Awingi linguistic rules and symbols.
    Returns metadata dictionary with model paths and verification telemetry.
    """
    if not SPM_AVAILABLE:
        raise RuntimeError(
            "sentencepiece is not installed in the active environment. "
            "Please install via: pip install sentencepiece"
        )

    if config is None:
        config = TokenizerConfig()

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    temp_train_path = prepare_training_text(corpus)
    target_prefix = str(output_path / model_prefix)

    try:
        # Build training command args
        spm_args = config.to_spm_args(
            input_path=temp_train_path,
            model_prefix=target_prefix,
        )

        # Train model
        spm.SentencePieceTrainer.train(spm_args)

        model_file = f"{target_prefix}.model"
        vocab_file = f"{target_prefix}.vocab"

        # Verify model loads and can encode special characters
        sp = spm.SentencePieceProcessor(model_file=model_file)
        test_sample = "Awi agawxi qutɨrsɨ ŋa."
        pieces = sp.encode(test_sample, out_type=str)
        ids = sp.encode(test_sample, out_type=int)
        roundtrip = sp.decode(ids)

        return {
            "status": "success",
            "model_path": model_file,
            "vocab_path": vocab_file,
            "vocab_size": sp.get_piece_size(),
            "sample_verification": {
                "input": test_sample,
                "pieces": pieces,
                "token_ids": ids,
                "roundtrip": roundtrip,
                "lossless": roundtrip.strip() == test_sample.strip(),
            },
        }
    finally:
        if os.path.exists(temp_train_path):
            os.remove(temp_train_path)


def main():
    """CLI runner for training Awingi SentencePiece tokenizer."""
    parser = argparse.ArgumentParser(description="Train Awingi SentencePiece subword tokenizer.")
    parser.add_argument("--corpus", type=str, help="Path to plaintext or JSONL corpus file.")
    parser.add_argument("--output-dir", type=str, default="models/tokenizer", help="Output directory.")
    parser.add_argument("--vocab-size", type=int, default=4000, help="Vocabulary size.")
    parser.add_argument("--model-type", type=str, choices=["bpe", "unigram"], default="bpe", help="Model type.")
    parser.add_argument("--from-db", action="store_true", help="Load all approved sentences from platform database.")
    args = parser.parse_args()

    if args.from_db:
        from src.platform.database import SessionLocal
        from src.platform.models import Sentence

        db = SessionLocal()
        try:
            records = (
                db.query(Sentence.normalized_text)
                .filter(Sentence.is_duplicate == False)
                .all()
            )
            corpus_lines = [r[0] for r in records if r[0]]
            print(f"Loaded {len(corpus_lines)} unique sentences from database.")
        finally:
            db.close()
        corpus_input = corpus_lines
    elif args.corpus:
        corpus_input = args.corpus
    else:
        print("Error: Specify either --corpus <path> or --from-db", file=sys.stderr)
        sys.exit(1)

    config = TokenizerConfig(
        vocab_size=args.vocab_size,
        model_type=args.model_type,
    )

    print(f"Training Awingi {config.model_type.upper()} tokenizer (vocab_size={config.vocab_size})...")
    result = train_sentencepiece(
        corpus=corpus_input,
        output_dir=args.output_dir,
        config=config,
    )
    print("Training Complete!")
    print(f"Model saved: {result['model_path']}")
    print(f"Vocab saved: {result['vocab_path']}")
    print("Sample Test:", result["sample_verification"])


if __name__ == "__main__":
    main()
