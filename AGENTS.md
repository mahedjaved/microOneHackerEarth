# AGENTS.md — microOne HackerEarth (MedRAGAssistant / CURA-Med)

## What this repo is

Medical RAG chatbot with uncertainty quantification (CURA-Med / SourceProof Medical).
FastAPI backend + Streamlit frontend. Active development — not a placeholder repo.

## Repo layout

- `backend/server/` — FastAPI app, routes, modules, config. This is the real entrypoint.
- `frontend/` — Streamlit UI. Depends on `API_URL` env var.
- `backend/tests/` — unit tests (pytest + TestClient).
- `tests/regression/` — Playwright-based integration/UI tests.
- `data/` — corpus, FAISS index, trained models. Mostly gitignored; prebuilt artifacts are present.
- `specs/` — speckit feature specs.
- `submission/` — hackathon deliverables (reproduction guide, changelog, trajectories).
- `.specify/` — speckit constitution, templates, PowerShell scripts.

## Shell and environment

- **OS:** Windows 11, **shell is PowerShell** (not bash). `ls`, `&&` chains in scripts, and bash-isms do not work.
- **Python:** backend uses Python 3.10 locally, 3.13 in Docker. Root `requirements.txt` includes `specify-cli` which requires Python 3.11+.
- **Venvs:** backend has its own `.venv/` (gitignored). Root `.venv/` is for speckit only.

## Exact commands

### Backend unit tests (fast, no services needed)

```powershell
cd backend
python -m pytest tests/ -v --tb=short
```

Expected: ~73 passed. Dummy keys in `backend/server/.env` are sufficient; Pinecone/Groq features degrade gracefully without real keys.

### Train verifier (required before UQ pipeline works)

```powershell
cd backend
python scripts/train_verifier.py
```

Artifacts land in `data/models/` and `data/training/`. These directories are gitignored but prebuilt artifacts are already present in the repo.

### End-to-end UQ pipeline test

```powershell
cd backend
python scripts/test_e2e.py
```

### Regression tests (requires running services)

```powershell
# Terminal 1: start backend
cd backend
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000

# Terminal 2: start frontend
cd frontend
streamlit run app.py

# Terminal 3: run tests
pytest tests/regression/ -v
```

UI tests need Playwright + Chromium:
```powershell
pip install pytest-playwright playwright
python -m playwright install chromium
```

### Speckit (run from repo root via root venv)

```powershell
.venv\Scripts\specify.exe <command>
```

Workflow order: constitution → specify → clarify → plan → checklist → tasks → analyze → implement → converge

## Project history and current state

The repo has evolved through several distinct phases documented in `docs/` and `guidance/`:

- **2026-08-30**: Comparative study framework implemented via speckit (`specs/003-comparative-study/`). Initial results showed UQ-RAG scoring lower than baselines (1.7 vs 2.36/2.5).
- **2026-09-02 to 2026-09-04**: Intensive debugging and expert review sessions (documented in `docs/chat_compilation_report.md`). Key findings:
  - Scoring bugs in `tests/comparative/scoring.py` crashed on `None` responses and ignored `disclaimer` field
  - Conformal predictor was a stub (`is_fitted = True` without fitting) — UQ pipeline silently fell back to baseline RAG
  - `backend/server/modules/output/` was gitignored by a broad `output/` rule
  - Comparative study runtime was >60 min due to `REQUEST_DELAY=5`, `MAX_RETRIES=3`, `timeout=90`
- **2026-09-03 to 2026-09-04**: Speckit lifecycle for Bayesian evidence-fusion refactor (`specs/001-bayesian-evidence-fusion/`). Core functions implemented and tested, but **not yet wired into live pipeline** (`query_handlers.py:305` still uses `max(probs)`).
- **Current state**: All 73 backend unit tests pass. UQ pipeline initializes on startup with prebuilt artifacts in `data/models/`. The comparative study has known scoring bugs with a revised scorer available in `guidance/eval_review_expert.md`.

## Critical gotchas

- **Do not run speckit outside `.venv`** — the CLI is not globally installed.
- **Root `requirements.txt` is not for backend runtime.** It mixes `specify-cli` (Python 3.11+) with backend deps. Install backend deps from `backend/server/requirements.txt` when using Python 3.10.
- **`backend/.gitignore` excludes `data/`, `models/`, `*.md`, `*.docx`.** Docs and data artifacts are not tracked in git. The hackathon PDF in `docs/` is gitignored and is the project's source of truth.
- **`backend/server/.env` exists with dummy keys** (gitignored). Do not commit real keys.
- **Frontend `API_URL` defaults to `http://127.0.0.1:8000`.** Override via `frontend/.env` when backend runs elsewhere.
- **Docker multi-stage uses Python 3.13-slim** and downloads `en_core_web_md` during build. Render free-tier build timeout is a known concern (15 min).
- **PII / injection features degrade gracefully** when Presidio or dependencies are missing — tests account for this.
- **`backend/server/modules/output/` was previously gitignored** by a broad `output/` rule in `backend/.gitignore`. Verify it is tracked before relying on fresh clones initializing the UQ pipeline.
- **Comparative study scoring has known bugs** (see `guidance/eval_review_expert.md` and `guidance/indepth_guidance.md`): `response_data.get("response", "").lower()` crashes on `None`; scorer ignores `disclaimer` field; API call and scoring share a try/except so crashes overwrite real responses. A revised scorer exists in `guidance/eval_review_expert.md`.
- **Conformal predictor was a stub** (`is_fitted = True` without fitting). `ConformalPredictor.from_quantile()` and `predict_set_from_probs()` were added but may not be wired into `query_handlers.py:305` yet — verify before trusting UQ pipeline output.
- **`run_artifact_id` is the canary for real UQ execution.** If it is `None` on a non-safety query, the request fell back to baseline RAG through an exception handler.
- **Bayesian refactor is partially implemented.** `compute_support_probability()` in `backend/server/modules/verifier/bayesian_fusion.py` has 8 passing tests, but `query_handlers.py:305` still uses `max(probs)`. See `specs/001-bayesian-evidence-fusion/tasks.md` for T026–T034 convergence tasks.

## Architecture

- Backend entrypoint: `backend/server/main.py` — mounts routers for upload, ask, baselines, health, metrics.
- UQ pipeline initializes on startup (`_init_uq_pipeline`) loading models from `data/models/`.
- Config: `backend/server/config.py` via `pydantic_settings`. All env vars validated at startup.
- Frontend is a thin Streamlit shell (`frontend/app.py`) delegating to components.

## Testing quirks

- `pyproject.toml` at root sets `testpaths = ["tests/regression"]` with markers `slow`, `ui`, `api`. Backend unit tests live under `backend/tests/` and are not picked up by root pytest config.
- Regression tests use Playwright `sync_playwright` with headless Chromium. They wait for backend/frontend health endpoints with 30s timeout.
- `tests/regression/conftest.py` creates a minimal valid PDF fixture inline — no external fixture files needed for most tests.

## Research engineering rules

For scientifically significant changes, consult both:
1. `research-supervisor` — diagnosis, hypothesis evaluation, scientific reasoning.
2. `research-reviewer` — independent validation of proposed fix before declaring resolved.

Do not declare a significant change complete based solely on passing tests.

## Submission constraints

- No private data or credentials in submission.
- Every result claim must link to evidence in `submission/`.
- Judges must be able to reproduce from clone.
