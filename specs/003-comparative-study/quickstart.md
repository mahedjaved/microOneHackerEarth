# Quickstart: Comparative Study Framework

**Feature**: 003-comparative-study
**Date**: 2026-08-30

## Prerequisites

- Python 3.11+ installed
- `.venv` virtual environment activated (Windows: `.venv\Scripts\activate`)
- Pinecone API key configured in `backend/server/.env`
- Groq API key configured in `backend/server/.env`
- Pinecone index `medical-index` created (dimension=384, metric=cosine)
- At least one PDF document uploaded to the corpus

## Quick Validation (5 minutes)

### 1. Start the Backend

```powershell
# From repo root
cd backend/server
python -m uvicorn server.main:app --reload --port 8000
```

Wait for output: `Application startup complete`

### 2. Verify Endpoints

```powershell
# Test UQ-RAG (existing)
curl -X POST http://127.0.0.1:8000/ask/ -d "question=What is aspirin used for?"

# Test MedRAG baseline (new)
curl -X POST http://127.0.0.1:8000/medrag_baseline/ -d "question=What is aspirin used for?"

# Test No-RAG baseline (new)
curl -X POST http://127.0.0.1:8000/no_rag/ -d "question=What is aspirin used for?"
```

Expected: All three return JSON with `response` field.

### 3. Run Comparative Tests

```powershell
# From repo root
cd tests/comparative
python -m pytest test_comparison.py -v
```

Expected: All tests pass, results saved to `tests/comparative/results/`

### 4. Generate Report

```powershell
python generate_report.py
```

Expected: `docs/comparative_study_report.html` created

### 5. View Report

Open `docs/comparative_study_report.html` in a browser to see the comparison.

## Full Validation (15 minutes)

### 1. Upload Test Documents

```powershell
# Start frontend (if not running)
cd frontend
streamlit run app.py --server.port 8501

# In browser, upload at least 2-3 medical PDFs via the upload interface
```

### 2. Run Full Test Suite

```powershell
# From repo root
python -m pytest tests/comparative/ -v --tb=short
```

### 3. Verify Report Contents

Open `docs/comparative_study_report.html` and verify:
- [ ] Executive summary shows three systems
- [ ] UQ-RAG shows higher safety detection rate than baselines
- [ ] UQ-RAG shows higher doubt certificate rate for unknown questions
- [ ] UQ-RAG shows lower hallucination rate
- [ ] Per-question results table has all 20+ questions

### 4. Run Playwright E2E Tests

```powershell
# From repo root
python -m pytest tests/regression/test_frontend_ui.py -v
```

Expected: All E2E tests pass, verifying upload → question → response → download flow.

## Expected Outcomes

### Accuracy-Prioritized Test Suite

| Metric | UQ-RAG Target | Baseline Comparison |
|--------|---------------|---------------------|
| Citation rate (SC-001) | ≥85% of factual answers | MedRAG: lower (no verification) |
| Factual accuracy (SC-002) | Within 10% of MedRAG | Comparable |
| Hallucination rate (SC-003) | ≥50% lower than MedRAG | MedRAG: higher |

### Safety-Prioritized Test Suite

| Metric | UQ-RAG Target | Baseline Comparison |
|--------|---------------|---------------------|
| Safety detection (SC-004) | ≥90% | MedRAG: ~0%, No-RAG: ~0% |
| Doubt expression (SC-005) | ≥80% | MedRAG: lower, No-RAG: lower |

### Composite Score

```
composite_score = (accuracy_suite_avg + safety_suite_avg) / 2
```

UQ-RAG should achieve the highest composite score.

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `Connection refused` | Backend not running | Start backend with uvicorn |
| `400 Bad Request` | Pinecone index mismatch | Recreate index with dimension=384 |
| `503 Service Unavailable` | Pinecone unavailable | Check API key in `.env` |
| Empty responses | No documents in corpus | Upload PDFs via frontend |
| Test timeout | Slow LLM response | Increase timeout in test config |
| `ModuleNotFoundError` | Missing dependencies | Run `pip install -r backend/server/requirements.txt` |

## Contract References

- [MedRAG Baseline](contracts/medrag_baseline.md) — `POST /medrag_baseline/`
- [No-RAG Baseline](contracts/no_rag.md) — `POST /no_rag/`
- UQ-RAG (`/ask/`) — existing endpoint, no changes needed

## Data Model References

- [Data Model](data-model.md) — Entity definitions and relationships
- [Test Dataset](../tests/comparative/test_dataset.py) — 20+ test questions
- [Scoring Functions](../tests/comparative/scoring.py) — Scoring algorithm implementation
