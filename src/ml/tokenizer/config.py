"""
Awingi NLP Platform — Tokenizer Configuration
Defines linguistic symbol sets, special tokens, and training hyperparameters
for Awingi (Awngi, ISO 639-3: awn) SentencePiece subword tokenization.
"""

from dataclasses import dataclass, field
from typing import List


# Special orthographic symbols distinctive to Awingi orthography (Latin & Ethiopic)
AWINGI_SPECIAL_SYMBOLS = [
    "ɨ",  # Latin Small Letter I with Stroke (high central vowel /ɨ/)
    "Ɨ",  # Latin Capital Letter I with Stroke
    "ŋ",  # Latin Small Letter Eng (velar nasal /ŋ/)
    "Ŋ",  # Latin Capital Letter Eng
    "'",  # Glottal stop / ejective marker
]

# Ethiopic punctuation markers encountered in Ge'ez orthography
ETHIOPIC_PUNCTUATION = [
    "፡",  # Word separator (hudka)
    "።",  # Full stop (arat neteb)
    "፣",  # Comma (netela serez)
    "፤",  # Semicolon (dirib serez)
    "፥",  # Colon
    "፦",  # Preface
    "፧",  # Question mark
    "፨",  # Paragraph mark
]

# Special model tokens standard across HuggingFace / modern transformer architectures
DEFAULT_SPECIAL_TOKENS = {
    "pad_token": "<pad>",
    "unk_token": "<unk>",
    "bos_token": "<s>",
    "eos_token": "</s>",
    "mask_token": "<mask>",
}


@dataclass
class TokenizerConfig:
    """Configuration for training and evaluating an Awingi subword tokenizer."""

    vocab_size: int = 4000
    model_type: str = "bpe"  # "bpe" or "unigram"
    character_coverage: float = 0.9995
    byte_fallback: bool = True
    hard_vocab_limit: bool = False
    split_by_whitespace: bool = True
    split_by_unicode_script: bool = True
    normalization_rule_name: str = "nmt_nfkc"
    user_defined_symbols: List[str] = field(
        default_factory=lambda: list(AWINGI_SPECIAL_SYMBOLS)
    )
    pad_id: int = 0
    unk_id: int = 1
    bos_id: int = 2
    eos_id: int = 3
    pad_piece: str = "<pad>"
    unk_piece: str = "<unk>"
    bos_piece: str = "<s>"
    eos_piece: str = "</s>"

    def to_spm_args(self, input_path: str, model_prefix: str) -> str:
        """Serializes configuration into a SentencePiece trainer argument string."""
        symbols_str = ",".join(self.user_defined_symbols)
        return (
            f"--input={input_path} "
            f"--model_prefix={model_prefix} "
            f"--vocab_size={self.vocab_size} "
            f"--model_type={self.model_type} "
            f"--character_coverage={self.character_coverage} "
            f"--byte_fallback={'true' if self.byte_fallback else 'false'} "
            f"--hard_vocab_limit={'true' if self.hard_vocab_limit else 'false'} "
            f"--split_by_whitespace={'true' if self.split_by_whitespace else 'false'} "
            f"--split_by_unicode_script={'true' if self.split_by_unicode_script else 'false'} "
            f"--normalization_rule_name={self.normalization_rule_name} "
            f"--user_defined_symbols={symbols_str} "
            f"--pad_id={self.pad_id} "
            f"--unk_id={self.unk_id} "
            f"--bos_id={self.bos_id} "
            f"--eos_id={self.eos_id} "
            f"--pad_piece={self.pad_piece} "
            f"--unk_piece={self.unk_piece} "
            f"--bos_piece={self.bos_piece} "
            f"--eos_piece={self.eos_piece}"
        )
