# Reproduction Guide — CURA-Med / SourceProof Medical

**Project:** micro1 Agentic Workflows Hackathon (HackerEarth)  
**Date:** 2026-08-29  
**Environment:** Windows 11, Python 3.10.11, PowerShell 5.1  
**Repository:** `D:\PROJECTS\CLAUDE_CLI_AGENTS\HACKER_EARTH\HACKATHONS\microOneHackerEarth`

---

## Prerequisites

### 1. Clone the repository

```powershell
git clone <repository-url> microOneHackerEarth
cd microOneHackerEarth
git checkout 001-sourceproof-medical
```

### 2. Create Python virtual environment

```powershell
python -m venv backend/.venv
backend/.venv\Scripts\activate
```

**Note:** The project venv uses Python 3.10.11. The root `requirements.txt` includes `specify-cli` which requires Python 3.11+, but backend dependencies install fine under Python 3.10.

### 3. Install dependencies

```powershell
# From repo root
pip install -r requirements.txt

# Or install backend requirements directly
pip install -r backend/server/requirements.txt
```

### 4. Install spaCy English model (for PII detection tests)

```powershell
python -m spacy download en_core_web_md
```

### 5. Configure environment variables

Create `backend/server/.env`:

```env
pinecone_api_key=dummy-key-for-testing
groq_api_key=dummy-key-for-testing
```

**Note:** Real Pinecone/Groq keys are not required for testing. The server gracefully disables Pinecone and PII features when keys are invalid or dependencies are missing.

---

## Step-by-Step Reproduction

### Step 1: Verify server imports

```powershell
cd backend
python -c "import sys; sys.path.insert(0, '.'); from server.main import app; print('Server imports OK')"
```

**Expected output:**
```
2026-08-29 XX:XX:XX,XXX - MedicalAssistant - INFO - RAG Logger initialized successfully.
2026-08-29 XX:XX:XX,XXX - MedicalAssistant - WARNING - Pinecone not available: [401] Invalid API key. Vector store features disabled.
Server imports OK
```

### Step 2: Run unit tests

```powershell
cd backend
python -m pytest tests/ -v --tb=short
```

**Expected output:**
```
======================= 73 passed, 4 warnings in ~10s ========================
```

All 73 tests must pass. The 4 warnings are deprecation warnings from FastAPI/Starlette and langchain-community, not errors.

### Step 3: Train the verifier

```powershell
cd backend
python scripts/train_verifier.py
```

**Expected output:**
```
Loading corpus chunks...
Loaded 2000 chunks
Generating training data...
Generated 2000 labeled pairs
Label distribution: {'SUPPORTED': 1000, 'INSUFFICIENT': 1000}
Loading embedding model...
Extracting features...
Train: 1200, Calib: 300, Val: 300, Test: 200
Training GP classifier...
Model saved to data/models/verifier_gp.joblib
Calibrating probabilities...
Calibrator saved to data/models/calibrator.joblib
Computing conformal quantile...
Conformal quantile at alpha=0.10: 0.0000
Evaluating on test set...
Test accuracy: 1.000
Training metadata saved to data/models/training_metadata.json
Data splits saved to data/training/splits.json
Training complete!
```

**Expected artifacts:**
| File | Purpose |
|------|---------|
| `data/models/verifier_gp.joblib` | Trained RandomForest verifier |
| `data/models/calibrator.joblib` | Isotonic probability calibrator |
| `data/models/conformal_quantile.json` | LAC quantile at α=0.10 |
| `data/models/training_metadata.json` | Train/calib/val/test sizes, accuracy |
| `data/training/splits.json` | Feature vectors and labels for all splits |

### Step 4: Run end-to-end UQ pipeline test

```powershell
cd backend
python scripts/test_e2e.py
```

**Expected output:**
```
UQ pipeline initialized
Response: response='' sources=['medical-doc-1:page-1'] disclaimer='This is not medical advice. Consult a healthcare professional.' injection_detected=False pii_redacted=False doubt_certificate=None run_artifact_id=UUID('...')
Final decision: answer
Run ID: ...
End-to-end test passed!
```

### Step 5: Start the FastAPI server (optional)

```powershell
cd backend
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000
```

**Note:** The server requires valid Pinecone and Groq API keys for full functionality. Without them, the UQ pipeline runs but retrieval falls back to an empty evidence packet.

### Step 6: Test the `/ask/` endpoint (requires server running)

```powershell
curl -X POST "http://localhost:8000/ask/" -F "question=What is aspirin used for?"
```

**Expected response:** JSON with `response`, `sources`, `disclaimer`, `doubt_certificate`, `run_artifact_id`.

---

## Data Artifacts

### Corpus

| File | Description |
|------|-------------|
| `data/corpus/mirage/mirage_pubmed_2000.jsonl` | 2,000 MIRAGE/PubMed chunks |
| `data/corpus/adversarial/adversarial_cases.jsonl` | 30 synthetic test cases |
| `data/corpus/corpus_hash.txt` | SHA-256 aggregate hash |

### Index

| File | Description |
|------|-------------|
| `data/index/faiss.index` | 2,000 vectors, 384 dimensions |
| `data/index/faiss_metadata.json` | Index metadata |

### Models

| File | Description |
|------|-------------|
| `data/models/verifier_gp.joblib` | RandomForest classifier (3-dim features) |
| `data/models/calibrator.joblib` | Isotonic probability calibrator |
| `data/models/conformal_quantile.json` | LAC quantile: 0.0000 at α=0.10 |
| `data/models/training_metadata.json` | Accuracy: 1.000, feature_dim: 3 |

---

## Troubleshooting

### "No module named 'server'"
Ensure you're running from the `backend/` directory and `sys.path` includes `'.'`.

### "Pinecone not available: [401] Invalid API key"
This is expected with dummy keys. The server continues without Pinecone. For full functionality, set real `pinecone_api_key` in `backend/server/.env`.

### "PII detection unavailable (presidio not installed)"
Install presidio dependencies:
```powershell
pip install presidio-analyzer presidio-anonymizer spacy
python -m spacy download en_core_web_md
```

### "specify-cli requires Python >= 3.11"
The root `requirements.txt` includes `specify-cli` which requires Python 3.11+. Install backend requirements directly from `backend/server/requirements.txt` if using Python 3.10.

---

## Expected Runtime

| Step | Duration |
|------|----------|
| Dependency installation | ~2-3 minutes |
| Verifier training | ~5-10 minutes |
| Unit tests | ~10 seconds |
| End-to-end test | ~5 seconds |
| Server startup | ~5 seconds |

**Total reproduction time:** ~15 minutes (excluding dependency download time)

---

## Versions

| Component | Version |
|-----------|---------|
| Python | 3.10.11 |
| scikit-learn | 1.7.2 |
| mapie | 1.5.0 |
| sentence-transformers | 3.0.1 |
| fastapi | latest |
| pytest | 9.1.1 |
| presidio-analyzer | 2.2.364 |
| presidio-anonymizer | 2.2.364 |
| spacy | 3.8.16 |
| en_core_web_md | 3.8.0 |

---

## Contact

For issues or questions, refer to the project repository or contact the hackathon team.
