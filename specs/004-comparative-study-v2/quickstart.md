# Quickstart: Comparative Study v2

**Feature:** 004-comparative-study-v2
**Date:** 2026-08-30

## Prerequisites

- Docker services running (backend, qdrant, postgres)
- Python 3.10+ with pytest
- Pinecone index populated with documents
- Groq API key configured

## Quick Validation (15 minutes)

### 1. Verify Services

```powershell
# Check backend health
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health"
# Expected: {"status":"healthy","version":"1.0",...}
```

### 2. Run Single Test

```powershell
# Set PYTHONPATH
$env:PYTHONPATH="D:\PROJECTS\CLAUDE_CLI_AGENTS\HACKER_EARTH\HACKATHONS\microOneHackerEarth"

# Run single question test
python -c "
import requests
r = requests.post('http://127.0.0.1:8000/medrag_baseline/', data={'question': 'According to the aspirin document, what is the maximum single adult dose?'})
print(r.json()['response'][:200])
"
```

### 3. Run Full Comparative Study

```powershell
# Set PYTHONPATH
$env:PYTHONPATH="D:\PROJECTS\CLAUDE_CLI_AGENTS\HACKER_EARTH\HACKATHONS\microOneHackerEarth"

# Clear old results
Remove-Item "tests/comparative/results/*.json" -Force -ErrorAction SilentlyContinue

# Run all tests (3 runs with delays)
python tests/comparative/run_all.py
```

### 4. Generate Report

```powershell
python tests/comparative/generate_report.py
```

### 5. View Report

Open `docs/comparative_study_report_v2.html` in browser.

## Expected Outcomes

### Scoring Results (Target)

| System | Mean Score | Std Dev | 95% CI |
|--------|------------|---------|--------|
| UQ-RAG | 0.75-0.85 | <0.1 | [0.70, 0.90] |
| MedRAG | 0.55-0.65 | <0.1 | [0.50, 0.70] |
| No-RAG | 0.35-0.45 | <0.1 | [0.30, 0.50] |

### Safety Detection

| System | Safety Rate |
|--------|-------------|
| UQ-RAG | ≥90% |
| MedRAG | ~0% |
| No-RAG | ~0% |

### Calibration

| System | ECE |
|--------|-----|
| UQ-RAG | <0.1 |
| MedRAG | N/A |
| No-RAG | N/A |

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| HTTP 429 | Rate limit | Add longer delays in run_all.py |
| HTTP 500 | Backend error | Check docker logs backend-server-1 |
| Empty results | No documents | Upload PDFs via frontend |
| Low scores | Check keywords | Verify keywords match document content |

## Contract References

- [Scoring Functions](contracts/scoring.md) - Scoring system specification

## Data Model References

- [Data Model](../data-model.md) - Entity definitions and relationships
