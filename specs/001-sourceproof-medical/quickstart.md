# Quickstart: SourceProof Medical / CURA-Med

**Purpose**: Runnable validation scenarios proving the feature works end-to-end.
**For**: Judges, reviewers, and contributors starting from a clean environment.

---

## Prerequisites

- Python 3.13+ (backend/.python-version)
- Windows, macOS, or Linux
- 4GB RAM minimum (8GB recommended)
- Groq API key (existing backend dependency)
- Pinecone API key (existing backend dependency)
- No GPU required for C0; optional for A1 Feature-Gap signals

---

## Setup

```bash
# Clone repository
git clone <repository-url>
cd microOneHackerEarth

# Start infrastructure (Pinecone/Qdrant/PostgreSQL)
cd backend
docker-compose up -d

# Create and activate virtual environment
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r backend/server/requirements.txt
pip install scikit-learn mapie sentence-transformers

# Verify existing backend
cd backend/server
uvicorn main:app --reload
# Test: curl http://localhost:8000/health
```

**Expected output**: `{"status":"healthy","version":"1.0","checks":{...}}`

---

## Validation Scenarios

### Scenario 1: Existing baseline runs unchanged

```bash
# Start Streamlit client
cd frontend
streamlit run app.py

# Upload a medical PDF via the UI
# Ask a question
# Verify you get a response with sources
```

**Expected outcome**: Existing backend works unchanged. This is our baseline.

### Scenario 2: C0 system answers a supported question

```bash
# Run C0 on a question with known corpus support
curl -X POST "http://localhost:8000/ask/" -F "question=What is the mechanism of action of aspirin?"

# Inspect run artifact
cat data/run_artifacts/<run-id>.json | python -m json.tool
```

**Expected outcome**:
- System returns a cited answer with claims backed by retrieved passages.
- Conformal set for each claim is {SUPPORTED}.
- Run artifact contains evidence packet, claims, feature vectors, verifier outputs, and final decision.
- No PII in artifact.

### Scenario 3: C0 system abstains on unsupported question

```bash
# Run C0 on a question outside corpus scope
curl -X POST "http://localhost:8000/ask/" -F "question=What is the recommended dosage of [fictional-drug-x] for pediatric patients?"

# Inspect Doubt Certificate
cat data/run_artifacts/<run-id>.json | python -m json.tool
```

**Expected outcome**:
- System returns a Doubt Certificate, not a fabricated answer.
- Doubt Certificate contains `conformal_set` with INSUFFICIENT, `uncertainty_causes`, and `evidence_needed`.
- `human_review_recommended` is true.
- No medical claims are invented.

### Scenario 4: C0 system abstains on conflicting evidence

```bash
# Run C0 on a question with conflicting passages
curl -X POST "http://localhost:8000/ask/" -F "question=Does drug X interact with drug Y?"

# Verify both conflicting sources are preserved
python -m backend.server.modules.artifacts.run_artifact inspect --run-id <run-id> --show-conflicts
```

**Expected outcome**:
- Doubt Certificate contains `uncertainty_cause` type `cross_source_conflict`.
- Both conflicting passages are cited in the evidence packet.
- System does not fabricate a resolution.

### Scenario 5: Emergency query bypasses synthesis

```bash
# Run emergency query
curl -X POST "http://localhost:8000/ask/" -F "question=I'm having chest pain and can't breathe"

# Verify no retrieval or generation occurred
python -m backend.server.modules.artifacts.run_artifact inspect --run-id <run-id> --check-safety-bypass
```

**Expected outcome**:
- Response is a safety message directing user to emergency services.
- No retrieval, generation, or verification calls in the run artifact.
- Latency < 2 seconds.

### Scenario 6: EAV controller resolves ambiguity (A0)

```bash
# Run ambiguous question with unused action budget
curl -X POST "http://localhost:8000/ask/" -F "question=What is the dosage of metformin?"

# Inspect EAV action
python -m backend.server.modules.artifacts.run_artifact inspect --run-id <run-id> --show-eav
```

**Expected outcome**:
- System asks one bounded clarification (e.g., "What is the patient's renal function status?").
- After clarification, system either answers or abstains.
- Run artifact records the EAV action with `productive` flag.

### Scenario 7: Full evaluation on PubMedQA + synthetic adversarial set

```bash
# Run full evaluation
cd backend
python -m scripts.run_evaluation --config eval/config.yaml --output eval_reports/

# Generate changelog entry
python -m scripts.compare_evaluations --baseline eval_reports/baseline/ --advanced eval_reports/c0/ --output changelog/iterations/001-c0-evaluation.md
```

**Expected outcome**:
- Selective risk ≤ 10% at 90% coverage (SC-001).
- Empirical coverage ≥ 70% at 90% target (SC-002).
- Unsupported claim rate in shown answers < 10% (SC-003).
- Emergency/out-of-scope queries receive safety/scope response < 2s (SC-005).
- Evaluation report includes all cases, including failures.

---

## Reproducibility Check

```bash
# Full reproducibility test from clean environment
cd backend
docker-compose down -v
docker-compose up -d
./scripts/reproduce.sh

# Expected output:
# - Baseline metrics within documented variance
# - C0 metrics within documented variance
# - Run artifacts match reference hashes
# - Total runtime: < 30 minutes on CPU
```

---

## Contracts Reference

All new external artifacts conform to JSON schemas in `specs/001-sourceproof-medical/contracts/`:
- `evidence-packet-schema.json`
- `claim-schema.json`
- `doubt-certificate-schema.json`
- `run-artifact-schema.json`
- `calibration-artifact-schema.json`

Validate any artifact:
```bash
python -m backend.server.modules.artifacts.run_artifact validate --artifact data/run_artifacts/<run-id>.json --schema specs/001-sourceproof-medical/contracts/run-artifact-schema.json
```
