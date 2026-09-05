# Quickstart: Bayesian Evidence Fusion for UQ-RAG

**Branch**: `001-bayesian-evidence-fusion`
**Date**: 2026-09-04
**Spec**: [../spec.md](../spec.md)
**Data model**: [../data-model.md](../data-model.md)
**Contracts**: [../contracts/contracts.md](../contracts/contracts.md)

This guide walks through the validation scenarios that prove the feature works
end-to-end. Each scenario maps to one or more success criteria in the spec.

## Prerequisites

- Python 3.11 in `.venv/` (already installed during the comparative-study fix)
- Backend dependencies installed (see `requirements.txt`)
- A running backend on `http://127.0.0.1:8000` (start with `uvicorn server.main:app` from `backend/`)
- The new calibration set at `tests/comparative/data/calibration_set.json` (created by this feature)

## Setup

```powershell
# From repo root
.venv\Scripts\python.exe -m pip install -r requirements.txt  # if not already done
cd backend
..\.venv\Scripts\python.exe -m uvicorn server.main:app --host 127.0.0.1 --port 8000
```

In a second terminal, from the repo root:

```powershell
# Optional: configure prior and cost ratio (defaults are 0.5 and 10:1)
$env:UQ_PRIOR = "0.5"
$env:UQ_COST_RATIO = "10:1"
```

## Scenario 1 — Honest accuracy reporting (SC-001, SC-002, FR-004, FR-005)

**Goal**: After running the comparative study, the report's `Accuracy-Suite Avg`
column matches the hand-computed mean of the D1–D6 per-question scores.

**Run**:
```powershell
cd C:\Users\ksfma\Downloads\Projects\AIEngineeringProjects\CLAUDE_CLI_AGENTS\HACKER_EARTH\HACKATHONS\microOneHackerEarth
.venv\Scripts\python.exe tests\comparative\run_study.py --suite original
.venv\Scripts\python.exe tests\comparative\generate_report.py
```

**Verify**:
1. Open `docs/comparative_study_report.html` in a browser.
2. The "Accuracy-Suite Avg" row in the "Accuracy-Prioritized Test Suite" table
   shows a **non-zero** value for at least one system (previously always 0.00).
3. The values in the "Per-Question Results" table for D1–D6, averaged by system,
   match the "Accuracy-Suite Avg" column to two decimal places.

**Expected**: UQ-RAG ~0.11, MedRAG ~0.84, No-RAG ~0.55 (the corrected picture
from the original honest run, not the buggy 0.00).

---

## Scenario 2 — Log-odds evidence fusion (SC-003, FR-001, FR-002, FR-003)

**Goal**: The new `compute_support_probability` function produces the three
reference-case outputs and matches the closed-form log-odds calculation.

**Run**:
```powershell
.venv\Scripts\python.exe -m pytest tests/comparative/test_bayesian_fusion.py -v
```

**Verify**: All three test cases pass:
1. `test_log_odds_agreement` — `(0.8, 0.9), (0.7, 0.85), prior=0.5` → posterior > 0.8
2. `test_log_odds_offtopic` — `(0.8, 0.9), (0.01, 0.85), prior=0.5` → posterior ≈ 0.8 (within 0.1)
3. `test_log_odds_neutral` — `(0.5, 0.9), (0.5, 0.85), prior=0.5` → posterior == 0.5 (exact)

**Expected**: 3 passed, 0 failed.

---

## Scenario 3 — Latency regression check (SC-007)

**Goal**: The new log-odds fusion adds <5 ms per claim versus the legacy
mean/max implementation.

**Run**:
```powershell
.venv\Scripts\python.exe -m pytest tests/comparative/test_bayesian_fusion.py::test_latency_regression -v
```

**Verify**: Test passes; the measured per-claim latency is < 5 ms on the
development machine.

**Note**: This is a regression check, not a new performance target. The
legacy `mean()`/`max()` was effectively free, and the new logic is O(n)
arithmetic over already-computed probabilities plus at most one
cosine-similarity call per claim.

---

## Scenario 4 — Conformal quantile reproducibility (SC-004, FR-006, FR-007)

**Goal**: The chosen conformal quantile is reproducible from the calibration
set and the cost ratio.

**Run**:
```powershell
.venv\Scripts\python.exe -m pytest tests/comparative/test_conformal_quantile.py -v
```

**Verify**: The test computes the quantile twice (once via the implementation,
once via a reference brute-force sweep) with the same inputs and asserts the
values are equal to within `1e-6`.

---

## Scenario 5 — DoubtCertificate schema bump (FR-010, FR-012)

**Goal**: The new optional fields are populated on the new code path and
`None` on the legacy path.

**Run**:
```powershell
# Start backend with new path enabled (default)
.venv\Scripts\python.exe -c "
import requests
r = requests.post('http://127.0.0.1:8000/ask/', data={'question': 'What is aspirin?'}, timeout=60)
cert = r.json().get('doubt_certificate', {})
print('prior:', cert.get('prior'))
print('combined_posterior:', cert.get('combined_posterior'))
print('relevance_weighted:', cert.get('relevance_weighted'))
"
```

**Verify**: All three fields are non-`None` (i.e., the new path is active).

**Then, to verify backwards compatibility**:
```powershell
$env:UQ_USE_BAYESIAN_FUSION = "0"
# Restart backend
.venv\Scripts\python.exe -c "
import requests
r = requests.post('http://127.0.0.1:8000/ask/', data={'question': 'What is aspirin?'}, timeout=60)
cert = r.json().get('doubt_certificate', {})
print('prior:', cert.get('prior'))
print('combined_posterior:', cert.get('combined_posterior'))
print('relevance_weighted:', cert.get('relevance_weighted'))
"
```

**Verify**: All three fields are `None` (legacy path is active).

---

## Scenario 6 — Boilerplate can't dominate (SC-005, FR-008, US4)

**Goal**: A claim with low cosine similarity to the question contributes
≤10% as much to the combined posterior as a high-relevance claim.

**Run**:
```powershell
.venv\Scripts\python.exe -m pytest tests/comparative/test_bayesian_fusion.py::test_boilerplate_dampening -v
```

**Verify**: The test passes; the boilerplate claim's contribution to the
posterior is at most 10% of the high-relevance claim's contribution.

---

## What "done" looks like

When all six scenarios pass:

1. `docs/comparative_study_report.html` shows the honest accuracy numbers
   (MedRAG ~0.84, UQ-RAG ~0.11, No-RAG ~0.55 on accuracy, not 0.00 across the
   board).
2. The verifier's `compute_support_probability` is principled, not
   ad hoc.
3. The conformal quantile is reproducible and audit-defensible.
4. The DoubtCertificate schema is backwards-compatible.
5. The boilerplate problem is handled by dampening, not by averaging.
6. The system is ready for the comparative-study report to be submitted with
   the honest story.

## See also

- `../spec.md` — Feature specification
- `../research.md` — Design decisions and alternatives considered
- `../data-model.md` — Entity definitions
- `../contracts/contracts.md` — API and module-level contracts
