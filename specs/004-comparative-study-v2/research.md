# Research: Comparative Study v2 - Rapid Remediation

**Feature:** 004-comparative-study-v2
**Date:** 2026-08-30

## Overview

This document resolves technical decisions for the rapid remediation of the comparative study framework.

## Research Items

### 1. Safety Scoring as Gating Criterion

**Decision:** Safety detection is binary pass/fail (1.0 or 0.0), not a scored dimension.

**Rationale:** 
- Current system penalizes UQ-RAG for correct abstention (-1)
- Safety is a requirement, not a preference
- Gating aligns with Constitution Article IV (emergency safety behavior)
- Prevents "gaming" by giving dangerous advice

**Alternatives considered:**
- Weighted scoring (0-3): Rejected because safety is non-negotiable
- Separate safety score: Rejected because it dilutes the importance

### 2. Document-Specific Question Design

**Decision:** Questions must require information from uploaded documents, not general knowledge.

**Rationale:**
- Current questions answerable from LLM training data
- Nullifies retrieval advantage
- Document-specific questions test what RAG systems are designed for

**Implementation:**
- Use phrases like "According to the document..."
- Reference specific document content (dosage, administration)
- Include questions where document explicitly does NOT contain answer

### 3. Normalized Scoring Scale

**Decision:** All scores normalized to [0, 1] interval.

**Rationale:**
- Current ordinal 0-3 scale violates measurement theory
- Normalized scores allow meaningful averaging
- Enables proper statistical analysis

**Formula:**
```
normalized = (raw_score - min_possible) / (max_possible - min_possible)
```

### 4. Calibration Metrics

**Decision:** Report Expected Calibration Error (ECE) with 10 bins.

**Rationale:**
- Demonstrates UQ-RAG confidence correlates with accuracy
- Standard metric in uncertainty quantification research
- Shows value of conformal prediction layer

**Formula:**
```
ECE = Σ |accuracy_bin - confidence_bin| * n_bin / N
```

### 5. Rate Limit Handling

**Decision:** Add 2-second delays between API requests.

**Rationale:**
- Groq rate limits caused test failures
- 2-second delay prevents 429 errors
- Adds ~40 seconds to full test run (acceptable)

### 6. Multiple Runs for Variance

**Decision:** Run tests 3 times, report mean ± SD.

**Rationale:**
- Single run has high variance
- 3 runs minimum for variance estimation
- Enables confidence interval reporting

## Technology Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Safety scoring | Binary gating | Constitution compliance |
| Question design | Document-specific | Test retrieval value |
| Scoring scale | [0, 1] normalized | Statistical validity |
| Calibration | ECE with 10 bins | Standard UQ metric |
| Rate limiting | 2s delays | Prevent 429 errors |
| Variance | 3 runs, mean ± SD | Reliability estimation |

## References

- Stevens, S.S. (1946). On the Theory of Scales of Measurement.
- Guo, C., et al. (2017). On Calibration of Modern Neural Networks.
- MedRAG Paper (ACL 2024): gzxiong/MedRAG
