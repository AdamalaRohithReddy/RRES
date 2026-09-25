# Unified AI Agent for Citizen Financial & Social Support

## Project Overview
The **Unified AI Agent for Citizen Financial & Social Support** is an open, modular platform designed to assist citizens in identifying and accessing verified government financial and social welfare schemes.

The full vision encompasses:
- Citizen Profile & Eligibility Rule Engine
- Document Intelligence & OCR Fallback
- Semantic Retrieval-Augmented Generation (RAG)
- Personalized Action Plans & Application Guidance
- Multilingual Interaction (including Indian Regional Languages & Voice)

---

## Milestone Status

| Milestone | Description | Status |
|---|---|---|
| **Milestone 1** | **RAG Foundation** (PDF Ingestion, Semantic Chunking, Embeddings, Qdrant Vector Store, Provenance Retrieval, Benchmark Evaluation) | **Completed & Verified** |
| Milestone 2 | Document Intelligence & OCR Engine Fallback | Planned |
| Milestone 3 | FastAPI AI Service & Spring Boot Backend Integration | Planned |
| Milestone 4 | Eligibility Reasoning Engine & Personalized Action Planning | Planned |
| Milestone 5 | Citizen Portal Frontend & Multilingual / Voice Support | Planned |

---

## Repository Structure

```
unified-ai-agent/
│
├── ai-service/             # [Milestone 1] Python RAG & Vector Search Service
│   ├── src/
│   │   ├── ingestion/      # PDF loader, PyMuPDF extraction, text cleaning, pipeline
│   │   ├── chunking/       # Semantic structure-aware chunker, metadata builder
│   │   ├── embeddings/     # Sentence Transformers configurable embedder
│   │   ├── vector_store/   # Qdrant client, collection manager, similarity search
│   │   ├── retrieval/      # Semantic query retriever, provenance formatter
│   │   ├── evaluation/     # 10-query benchmark dataset, Hit@K & MRR metrics
│   │   └── config/         # Pydantic environment configuration & settings
│   │
│   ├── data/
│   │   ├── raw/            # Official scheme PDFs (e.g. Atal Pension Yojana)
│   │   └── processed/      # Embedded Qdrant storage & metadata
│   │
│   ├── tests/              # 30 Unit and End-to-End integration tests
│   ├── requirements.txt    # Milestone 1 dependencies
│   ├── .env.example        # Environment variables template
│   └── README.md           # Comprehensive AI Service documentation
│
├── backend/                # [Milestone 3] Spring Boot Backend Service (Reserved)
├── frontend/               # [Milestone 5] Citizen Portal Web Application (Reserved)
├── docs/                   # Architecture decision records & design specifications
└── README.md               # Root repository documentation
```

---

## Quickstart — Milestone 1 (RAG Foundation)

### 1. Set up the Python Environment
```powershell
cd unified-ai-agent/ai-service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Ingest an Official Document
```powershell
python -m src.ingest_cli `
  --pdf data/raw/atal_pension_yojana_guidelines.pdf `
  --scheme-id APY `
  --scheme-name "Atal Pension Yojana" `
  --source-url "https://financialservices.gov.in/beta/en/scheme/atal-pension-yojana"
```

### 3. Query with Provenance
```powershell
python -m src.query_cli --query "What are the eligibility requirements?" --top-k 3
```

### 4. Run Tests & Evaluation
```powershell
# Run 30 unit & integration tests
pytest tests -v

# Run 10-query benchmark evaluation
python -m src.evaluation.evaluate
```

For complete implementation details, see [AI Service Documentation](ai-service/README.md).
