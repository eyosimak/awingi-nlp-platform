"""
Awingi NLP Platform — Dual-Orthography Corpus Compiler
Combines Ge'ez and Latin script Awingi linguistic materials into a unified,
normalized training corpus for subword tokenization and language modeling.
"""

import json
import re
from pathlib import Path
from src.pipeline.normalizer import normalize_text


def compile_dual_orthography_corpus(
    jsonl_path: Path,
    latin_txt_path: Path,
    output_path: Path,
) -> dict:
    """
    Merges Latin and Ge'ez data sources into a clean, normalized dual-script corpus.
    """
    sentences = set()
    geez_count = 0
    latin_count = 0

    # 1. Ingest Ge'ez records from JSONL
    if jsonl_path.exists():
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    text = data.get("text") or data.get("raw_text") or ""
                except Exception:
                    text = line
                clean = normalize_text(text)
                clean = re.sub(r"^\d+[,.\-]\s*", "", clean).strip()
                if clean and clean not in sentences:
                    sentences.add(clean)
                    geez_count += 1

    # 2. Ingest Latin records from plaintext
    if latin_txt_path.exists():
        with open(latin_txt_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                clean = normalize_text(line)
                clean = re.sub(r"^\d+[,.\-]\s*", "", clean).strip()
                if clean and clean not in sentences:
                    sentences.add(clean)
                    latin_count += 1

    # 3. Add foundational linguistic primer patterns (Latin orthography)
    primer_latin_sentences = [
        "Awi agawxi qutɨrsɨ kɨda ŋa.",
        "Deshta antɨ antɨki deshta aqwɨ.",
        "Awingi luwatsa gitsishi tsetsetsa.",
        "Bɨra bɨrki ŋuna kɨtɨma ts'ege.",
        "Yɨna katsa deski gwayta.",
        "Anbaŋ bɨsta antɨrsɨ.",
        "Gimbi kɨda yɨna lɨtsa.",
        "Kasa dɨnxɨwa bɨsta asha.",
        "Awi wereda dangila injibara fagita lekoma.",
        "Qoltsa bɨsta agawxi kawa.",
        "Awni luwa kɨda gitsishi ŋa.",
        "Agawxi qutɨrsɨ bɨra bɨrki ŋuna.",
        "Injibara kɨtɨma agaw awi zonda kɨda.",
        "Luwatsa tsetsetsa agawxi aqwɨ.",
        "Antɨ antɨki deshta aqwɨ kɨda.",
    ]
    for s in primer_latin_sentences:
        clean = normalize_text(s)
        if clean not in sentences:
            sentences.add(clean)
            latin_count += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for s in sorted(sentences):
            f.write(f"{s}\n")

    return {
        "total_sentences": len(sentences),
        "geez_sentences": geez_count,
        "latin_sentences": latin_count,
        "output_path": str(output_path),
    }


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent.parent
    stats = compile_dual_orthography_corpus(
        jsonl_path=root / "data" / "live_corpus.jsonl",
        latin_txt_path=root / "scripts" / "sample_data" / "sample_awingi_text.txt",
        output_path=root / "data" / "balanced_corpus.txt",
    )
    print("Dual-Orthography Corpus Compiled:")
    print(stats)
