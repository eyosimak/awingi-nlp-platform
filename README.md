# Awingi NLP Platform (awingi-nlp-platform)

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Pydantic: v2](https://img.shields.io/badge/Pydantic-v2-E92063.svg?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)

> **Development and Evaluation of a Language Model for Awingi with Agricultural Question Answering Application**  
> *Bachelor of Science in Computer Science Final Year Capstone Project*  
> **Institution:** Injibara University, College of Engineering and Technology, Department of Computer Science  
> **Collaborator:** Institute of Agaw Studies, Injibara University  
> **Language:** Awingi (Awngi) — Central Cushitic, ISO 639-3 `awn` (~1 Million speakers, Agew Awi Zone, Ethiopia)

---

## 1. Project Overview

Awingi is a Central Cushitic language spoken widely in northwestern Ethiopia with official primary school curricula (Grades 1–8) in a Latin-based orthography, but **zero computational representation** in modern language models or AI platforms.

This repository implements the complete engineering ecosystem to bridge this digital divide:
1. **Document Ingestion & Normalization Pipeline:** Extracts, cleans, deduplicates, and segments text from Institute of Agaw Studies soft-copy materials (PDF, DOCX, TXT).
2. **Web Review & Ingestion Platform:** FastAPI + Jinja2/Tailwind + SQLAlchemy application for batch ingestion, linguistic spot-checking, and dataset partitioning (`train.jsonl`, `val.jsonl`, `test.jsonl`).
3. **Subword Tokenizer & Model Training:** Custom SentencePiece BPE tokenizer and dual-track neural modeling (compact from-scratch Transformer and parameter-efficient NLLB-200 QLoRA).
4. **Agricultural Question Answering (RAG):** Context-grounded agronomic advisory tool for local Awingi farmers.

---

## 2. Dual-Computer Engineering Architecture

To enable high-velocity development across two developers without merge conflicts or code breakage, the codebase is partitioned into cleanly decoupled workspaces governed by a shared Pydantic contract:

```
awingi-nlp-platform/
├── src/
│   ├── common/             <-- 🤝 SHARED CONTRACT (schemas.py, config.py) - NEVER EDIT ALONE
│   │
│   ├── platform/           <-- 💻 COMPUTER 1 WORKSPACE (Platform & ML Lead)
│   │   ├── app.py          # FastAPI application
│   │   ├── database.py     # SQLAlchemy ORM engine & sessions
│   │   ├── models.py       # User, Document, Sentence tables
│   │   ├── auth/           # Session/JWT authentication & roles
│   │   ├── routes/         # Ingest API, Reviewer dashboard, Export engine
│   │   └── templates/      # Jinja2 HTML + Tailwind UI
│   │
│   ├── pipeline/           <-- 💻 COMPUTER 2 WORKSPACE (Ingestion & Data Lead)
│   │   ├── extractors/     # PyMuPDF, python-docx, TXT extractors
│   │   ├── normalizer.py   # Unicode NFKC + Awingi orthography preservation
│   │   ├── segmenter.py    # Awingi sentence boundary detector
│   │   ├── deduplicator.py # Exact hash deduplication
│   │   └── run_ingest.py   # CLI: python -m src.pipeline.run_ingest <folder>
│   │
│   └── ml/                 <-- 🧠 PHASE 2 (Model Training & RAG)
│       ├── tokenizer/      # SentencePiece training harness
│       ├── models/         # From-scratch Transformer architecture
│       └── rag/            # FAISS vector similarity search
│
├── tests/
│   ├── conftest.py         # Shared test fixtures
│   ├── test_contract.py    # Schema integrity tests
│   ├── test_platform/      # Computer 1 tests
│   └── test_pipeline/      # Computer 2 tests
│
└── data/                   # 🔒 LOCAL STORAGE ONLY (Never committed to Git)
    ├── raw/                # Institute soft-copies (copyrighted)
    ├── processed/          # Standardized JSON batches
    └── app.db              # SQLite development database
```

---

## 3. Quick Start (Both Computers)

### Step 1: Clone and Run Automated Setup
```bash
git clone <repository_url>
cd awingi-nlp-platform
bash scripts/setup_dev.sh
```

### Step 2: Manual Environment Setup (Alternative)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
pytest tests/ -v
```

---

## 4. Workflows

### Computer 2 Workflow: Document Processing
```bash
# 1. Place Institute files (PDF, DOCX, TXT) into data/raw/
# 2. Run extraction and print 50 random samples for linguistic review:
python -m src.pipeline.run_ingest data/raw/ --output data/processed/ --sample 50

# 3. Inspect generated JSON batches in data/processed/
```

### Computer 1 Workflow: Platform & Ingestion
```bash
# 1. Start development server:
uvicorn src.platform.app:app --reload

# 2. Import processed batches into database:
python scripts/import_batches.py data/processed/

# 3. Open browser at http://localhost:8000:
#    - View dashboard statistics
#    - Review and approve sentences at /review
#    - Export train/val/test splits at /api/export
```

---

## 5. Git Collaboration Rules

1. **Main Branch Protection:** `main` is always working, runnable code.
2. **Branch Per Feature:**
   - Computer 1: `git checkout -b feature/platform-<name>`
   - Computer 2: `git checkout -b feature/pipeline-<name>`
3. **Daily Sync Routine:**
   ```bash
   git checkout main
   git pull origin main
   git checkout feature/your-branch
   git merge main
   ```
4. **Never Commit Secrets or Raw Documents:** `data/raw/` and `data/app.db` are strictly `.gitignore`d.

---

## 6. Testing

Run all unit and contract tests:
```bash
pytest tests/ -v
```
