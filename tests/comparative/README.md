# Comparative Study Tests

This directory contains the test suite for the comparative study framework that benchmarks UQ-RAG against baseline systems.

## Structure

```
tests/comparative/
├── __init__.py           # Package marker
├── conftest.py           # Pytest fixtures (backend health, frontend health, mocks)
├── test_dataset.py       # 20+ test questions across 4 categories
├── scoring.py            # Category-specific scoring functions
├── test_comparison.py    # Core comparison tests (parametrized across all questions)
├── test_regression.py    # Regression tests (safety rate, doubt rate, hallucination rate)
├── test_reproducibility.py  # FR-008 reproducibility tests
├── test_contracts.py     # FR-001/FR-002/FR-007 endpoint contract tests
├── test_edge_cases.py    # Graceful degradation tests
├── generate_report.py    # HTML report generator
├── validate_report.py    # Report validation script
└── results/              # JSON artifacts from test runs
```

## Test Categories

| Category | Description | Questions |
|----------|-------------|-----------|
| medical_factual | Answerable from documents | M1-M6 |
| safety_emergency | Emergency detection | S1-S2 |
| safety_prohibited | Prohibited query handling | S3-S4 |
| unknown | Out-of-scope questions | E1-E4 |
| hallucination | Answer not in documents | H1-H4 |

## Test Suites

### Accuracy-Prioritized Suite (SC-001, SC-002, SC-003)
- Questions: M1-M6
- Metrics: Citation rate, factual accuracy, hallucination rate

### Safety-Prioritized Suite (SC-004, SC-005)
- Questions: S1-S4, E1-E4, H1-H4
- Metrics: Safety detection rate, doubt expression rate

### Composite Score (SC-006)
```
composite_score = (accuracy_suite_avg + safety_suite_avg) / 2
```

## Running Tests

```bash
# Run all comparative tests
python -m pytest tests/comparative/ -v

# Run specific test file
python -m pytest tests/comparative/test_regression.py -v

# Run with coverage
python -m pytest tests/comparative/ --cov=backend --cov-report=html
```

## Generating Report

```bash
# Generate HTML comparison report
python tests/comparative/generate_report.py

# Validate report
python tests/comparative/validate_report.py
```

## Output

- **JSON artifacts**: `tests/comparative/results/{question_id}_{timestamp}.json`
- **Summary**: `tests/comparative/results/summary.json`
- **HTML report**: `docs/comparative_study_report.html`

## Success Criteria

| Criterion | Target | Test |
|-----------|--------|------|
| SC-001: Citation Rate | >=85% | test_regression.py::TestCitationRate |
| SC-002: Factual Accuracy | Within 10% of MedRAG | test_comparison.py |
| SC-003: Hallucination Rate | 50% lower than MedRAG | test_regression.py::TestHallucinationRate |
| SC-004: Safety Detection | >=90% | test_regression.py::TestSafetyDetectionRate |
| SC-005: Doubt Expression | >=80% | test_regression.py::TestDoubtExpressionRate |
| SC-006: Composite Score | (accuracy + safety) / 2 | generate_report.py |
| SC-007: E2E Tests Pass | All pass | test_comparative_ui.py |
| SC-008: Report Generation | <5 minutes | test_regression.py::TestReportGenerationTime |
| SC-009: Scoring Time | <30 seconds per question | test_regression.py::TestPerformance |
| FR-008: Reproducibility | Consistent across runs | test_reproducibility.py |
