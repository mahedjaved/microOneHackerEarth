# Research: SourceProof Medical / CURA-Med

**Purpose**: Resolve all technical unknowns for extending the existing `backend/` with the CURA-Med UQ layer.
**Created**: 2026-08-28

---

## 1. Foundation: Existing backend

**Decision**: Extend the existing `backend/` FastAPI + Streamlit medical RAG system. Do not build from scratch.

**Rationale**:
- Existing codebase provides: FastAPI backend, Streamlit frontend, LangChain RAG chain (Groq/Llama 3.3 70B), Pinecone/Qdrant vector stores, Presidio PII detection, prompt-injection detection, LangSmith tracing, RAGAS evaluation, Prometheus/Grafana metrics, PostgreSQL logging, Docker/Compose, GitHub Actions CI/CD.
- The existing `/ask/` route already implements: prompt-injection check → PII redaction → retrieval → RAG chain → response with sources.
- Our contribution is the UQ layer (Articles XIII–XVII in the constitution): claim decomposition, evidence verification, conformal prediction, Doubt Certificate, EAV controller, structured run artifacts.

**What we extend in place**:
- `backend/server/modules/query_handlers.py` — insert UQ pipeline after retrieval
- `backend/server/routes/ask_question.py` — add new response types (Doubt Certificate)
- `backend/server/schemas.py` — add DoubtCertificate, RunArtifact, EAVAction schemas
- `backend/server/requirements.txt` — add scikit-learn, mapie, sentence-transformers

**What we add as new modules**:
- `backend/server/modules/safety/` — medical-scope gate, emergency detection
- `backend/server/modules/claims/` — claim composer, feature vector
- `backend/server/modules/verifier/` — GP classifier, calibration, conformal prediction
- `backend/server/modules/eav/` — controller, clarify, retrieve
- `backend/server/modules/output/` — answer composer, doubt certificate, safety response
- `backend/server/modules/artifacts/` — run artifact construction and redaction

---

## 2. Three-way verifier: Gaussian process classifier

**Decision**: Use `sklearn.gaussian_process.GaussianProcessClassifier` with `CalibratedClassifierCV` (isotonic regression) + MAPIE for split conformal prediction.

**Rationale**:
- Project owner prefers ML methods; GP is easy to train and provides calibrated probabilities.
- scikit-learn implementation is stable, well-documented, no external dependencies beyond numpy/scipy.
- MAPIE is MIT-licensed, actively maintained, scikit-learn-compatible.
- Existing backend already uses scikit-learn ecosystem (via langchain, pydantic).

**Implementation notes**:
- Feature vector from `claims/feature_vector.py` feeds the GP classifier.
- Training data: MedNLI (3-way entailment) or HealthVer as seed, augmented with synthetic adversarial cases.
- Probability calibration: `CalibratedClassifierCV` with isotonic regression.
- Four disjoint splits: training (fit GP), calibration (fit calibrator + compute conformal quantile), validation (tune thresholds), held-out test (final evaluation).

**Training data sources**:
- MedNLI: https://github.com/ming630/MedNLI
- HealthVer: https://github.com/ieee8023/HealthVer
- Synthetic adversarial cases (Article V governance)

---

## 3. Conformal prediction: MAPIE

**Decision**: Use `mapie` for split conformal classification.

**Rationale**:
- MIT-licensed, scikit-learn-compatible.
- Supports `SplitConformalClassifier` with LAC and APS score functions.
- Directly compatible with `GaussianProcessClassifier` + `CalibratedClassifierCV`.

**Implementation notes**:
- Alpha = 0.10 for 90% coverage (matching SC-002).
- Never fall back to top-probability label when set is ambiguous (Article XV).

---

## 4. Retrieval: extend existing Pinecone pipeline

**Decision**: Extend the existing Pinecone retriever in `load_vectorstore.py`. Add feature vector computation after retrieval.

**Rationale**:
- Existing code already implements: Pinecone serverless (production), Qdrant (local dev), `all-mpnet-base-v2` embeddings, top-k = 3 retrieval.
- Our addition: after retrieval, compute 8-block evidence feature vector for each claim-passage pair.
- Corpus: extend existing PDF-upload corpus with MIRAGE/PubMed abstract subset + synthetic adversarial set.

**Implementation notes**:
- Chunk size: extend existing 500-char chunks to 512-token chunks for PubMed abstracts.
- Top-k: keep existing top-k = 3 for baseline; evaluate top-k = 5–10 for advanced.
- Retrieval metadata: extend existing source metadata with top_score, score_margin, rank_dispersion.

---

## 5. Corpus: extend existing + add MIRAGE/PubMed + synthetic adversarial

**Decision**: Two-part corpus extending the existing PDF-upload corpus.

**Part 1 — Extend existing corpus with MIRAGE/PubMed**:
- Source: MIRAGE benchmark corpus (PubMed subset).
- Access: Download from MIRAGE HuggingFace: https://huggingface.co/datasets/MedRAG
- Processing: Extract title + abstract, chunk into 512-token passages, compute embeddings, index in Pinecone.
- Provenance: document title, PubMed ID, ingestion date, chunk ID, corpus hash.

**Part 2 — Synthetic adversarial case set**:
- Constructed by the project team.
- Types: no-evidence, conflicting-evidence, multi-hop, emergency-indicator, out-of-scope, ambiguous questions.
- Size: 30–50 cases.
- Storage: JSONL with question, expected abstention reason, expected conformal set, human-reviewed labels.

---

## 6. Baseline: existing backend unchanged

**Decision**: Baseline is the existing `backend/` RAG pipeline with no modifications.

**Implementation**:
- Same FastAPI `/ask/` endpoint, same Pinecone retriever, same Groq/Llama chain.
- Output: free-form answer with source filenames.
- No claim decomposition, no verification, no conformal prediction, no abstention.

**Evaluation**: Same questions, same model, same resource limits. Compare selective risk, answer accuracy, citation recall, latency.

---

## 7. Claim decomposition

**Decision**: Use LLM-based extraction (Groq/Llama) to decompose the answer into atomic claims.

**Rationale**:
- Existing backend already has Groq/Llama access. No new model dependency.
- MedRAGChecker uses NLI + KG for claim extraction, but we can use a simpler LLM-based approach for C0.
- If LLM-based extraction is insufficient, upgrade to NLI-based approach (MedRAGChecker pattern) for A0.

**Implementation notes**:
- Prompt Llama to decompose the answer into atomic claims with stable claim IDs and citation references.
- Output: list of `Claim` objects (defined in data-model.md).

---

## 8. Medical-scope safety gate

**Decision**: Extend existing prompt-injection detection with medical-scope classification.

**Rationale**:
- Existing code already has: prompt-injection heuristic, PII detection (Presidio).
- Add: emergency query detection (regex/keyword patterns), personal diagnosis/prescription detection (LLM classifier or keyword patterns), scope explanation for prohibited queries.
- Emergency queries bypass retrieval and generation entirely (Article IV).

**Implementation notes**:
- Add to `ask_question.py` before retrieval: scope check → emergency bypass or prohibited rejection.
- Reuse existing Presidio PII redaction.
- Log safety decisions in run artifact.

---

## 9. Calibration discipline

**Decision**: Four disjoint splits as specified in CURA-Med document.

**Splits**:
1. **Training** (60%): fit the three-way classifier.
2. **Calibration** (15%): fit probability calibrator + compute conformal quantile.
3. **Validation** (15%): tune EAV thresholds, select alpha, tune feature engineering.
4. **Held-out final test** (10%): evaluate once after architecture and thresholds are frozen.

**Rule**: Never tune on the held-out final test. If data is too small (<30 claim-evidence pairs per class), simplify and present as prototype.

---

## 10. Evaluation: extend existing RAGAS + add PubMedQA + MIRAGE

**Decision**: Extend existing RAGAS evaluation with PubMedQA and MIRAGE metrics.

**Existing**: RAGAS metrics, 51-pair medical Q&A set, CI regression gate.

**Add**:
- PubMedQA: 1,000 expert-labeled questions. Convert free-text output to yes/no/maybe using deterministic classifier.
- MIRAGE: 7,663 questions across 5 datasets. Compare retrieval metrics (Recall@k, nDCG@k) against MedRAG toolkit results.
- Synthetic adversarial set: evaluate abstention rate, Doubt Certificate quality, EAV productive-action rate.

---

## 11. HuggingFace model for verifier

**Decision**: Primary path is scikit-learn Gaussian process on engineered features. HuggingFace model is optional fallback.

**Candidate models** (if training data insufficient):
- `microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract`
- `dmis-lab/biobert-base-cased-v1.2`

**Selection rule**: If ≥200 labeled claim-evidence pairs, use GP. If <200, fine-tune PubMedBERT. If <50, fall back to prompted LLM with structured output.

**Status**: NEEDS VERIFICATION during implementation.

---

## Decisions Summary

| Unknown | Decision | Rationale |
|---------|----------|-----------|
| Foundation | Extend existing `backend/` | Real FastAPI + Streamlit + LangChain + Pinecone + Presidio + LangSmith + RAGAS + Docker/CI-CD already exists |
| Verifier | sklearn GaussianProcessClassifier + CalibratedClassifierCV + MAPIE | User preference for ML; calibrated probabilities; offline; reproducible |
| Retrieval | Extend existing Pinecone pipeline | Already implements dense retrieval with `all-mpnet-base-v2`; add feature vector computation |
| Corpus | Extend existing + MIRAGE/PubMed + synthetic adversarial set | External comparability + controlled UQ stress tests |
| Evaluation | Extend existing RAGAS + PubMedQA + MIRAGE + synthetic adversarial | Aligned with evidence-grounded free-text goal |
| Baseline | Existing `backend/` unchanged | Fair comparison, same corpus and model |
| Claim decomposition | LLM-based extraction via existing Groq/Llama | No new model dependency; upgrade to NLI if needed |
| Safety gate | Extend existing prompt-injection + PII with medical-scope | Reuses Presidio and existing heuristic |
| HuggingFace model | GP primary; PubMedBERT fallback if data insufficient | User preference + data-dependent |
