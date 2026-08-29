# Unit Test Report

**Generated:** 2026-08-29 08:29 UTC  
**Environment:** Windows 11, Python 3.10.11, pytest 9.1.1  
**Test Runner:** pytest with asyncio plugin  
**Branch:** 001-sourceproof-medical

---

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | 73 |
| Passed | 73 |
| Failed | 0 |
| Skipped | 0 |
| Pass Rate | 100% |

---

## Test Results by File

### `tests/test_health.py` (2/2 passed)

| Test | Status |
|------|--------|
| `test_health_endpoint_returns_200` | ✅ PASSED |
| `test_health_endpoint_has_expected_structure` | ✅ PASSED |

---

### `tests/test_pii_detector.py` (7/7 passed)

| Test | Status |
|------|--------|
| `test_clean_medical_query_passes` | ✅ PASSED |
| `test_patient_id_is_redacted` | ✅ PASSED |
| `test_mrn_is_redacted` | ✅ PASSED |
| `test_disabled_mode_skips_redaction` | ✅ PASSED |
| `test_strict_mode_raises_422` | ✅ PASSED |
| `test_mask_mode_produces_masked_output` | ✅ PASSED |
| `test_non_pii_text_passes_through` | ✅ PASSED |

---

### `tests/test_prompt_injection_detector.py` (4/4 passed)

| Test | Status |
|------|--------|
| `test_clean_query_passes` | ✅ PASSED |
| `test_jailbreak_pattern_is_blocked` | ✅ PASSED |
| `test_disabled_mode_skips_validation` | ✅ PASSED |
| `test_multiple_patterns_blocked` | ✅ PASSED |

---

### `tests/test_safety_gate.py` (13/13 passed)

| Test | Status |
|------|--------|
| `test_emergency_chest_pain` | ✅ PASSED |
| `test_emergency_heart_attack` | ✅ PASSED |
| `test_emergency_suicide` | ✅ PASSED |
| `test_emergency_overdose` | ✅ PASSED |
| `test_prohibited_diagnosis` | ✅ PASSED |
| `test_prohibited_prescription` | ✅ PASSED |
| `test_prohibited_patient_specific_risk` | ✅ PASSED |
| `test_prohibited_prescribe` | ✅ PASSED |
| `test_allowed_general_question` | ✅ PASSED |
| `test_allowed_medical_information` | ✅ PASSED |
| `test_emergency_unconscious` | ✅ PASSED |
| `test_emergency_severe_bleeding` | ✅ PASSED |
| `test_prohibited_multiple_flags` | ✅ PASSED |

---

### `tests/test_corpus_loader.py` (7/7 passed)

| Test | Status |
|------|--------|
| `test_sha256_file` | ✅ PASSED |
| `test_sha256_string` | ✅ PASSED |
| `test_compute_corpus_hash` | ✅ PASSED |
| `test_compute_corpus_hash_empty` | ✅ PASSED |
| `test_load_corpus_chunks` | ✅ PASSED |
| `test_load_corpus_chunks_empty` | ✅ PASSED |
| `test_build_evidence_packet` | ✅ PASSED |

---

### `tests/test_claims_composer.py` (4/4 passed)

| Test | Status |
|------|--------|
| `test_decompose_simple_answer` | ✅ PASSED |
| `test_decompose_empty_answer` | ✅ PASSED |
| `test_decompose_single_sentence` | ✅ PASSED |
| `test_match_citations` | ✅ PASSED |

---

### `tests/test_verifier_modules.py` (9/9 passed)

| Test | Status |
|------|--------|
| `test_train_and_predict_binary` | ✅ PASSED |
| `test_predict_returns_verifier_result` | ✅ PASSED |
| `test_predict_without_embedding_model_raises` | ✅ PASSED |
| `test_predict_without_training_raises` | ✅ PASSED |
| `test_save_and_load` | ✅ PASSED |
| `test_fit_and_transform` | ✅ PASSED |
| `test_transform_normalizes` | ✅ PASSED |
| `test_save_and_load` | ✅ PASSED |
| `test_fit_and_predict_set` | ✅ PASSED |
| `test_predict_set_returns_sets` | ✅ PASSED |
| `test_predict_quantile` | ✅ PASSED |
| `test_predict_set_without_fit_raises` | ✅ PASSED |

---

### `tests/test_eav_controller.py` (10/10 passed)

| Test | Status |
|------|--------|
| `test_no_action_for_singleton_supported` | ✅ PASSED |
| `test_clarify_for_missing_entities` | ✅ PASSED |
| `test_clarify_for_underspecified_scope` | ✅ PASSED |
| `test_retrieve_for_low_top_score` | ✅ PASSED |
| `test_retrieve_for_low_claim_coverage` | ✅ PASSED |
| `test_retrieve_for_conflict` | ✅ PASSED |
| `test_no_action_when_budget_exhausted` | ✅ PASSED |
| `test_record_action` | ✅ PASSED |
| `test_record_action_not_productive` | ✅ PASSED |
| `test_reset_budget` | ✅ PASSED |

---

### `tests/test_output_modules.py` (6/6 passed)

| Test | Status |
|------|--------|
| `test_build_doubt_certificate_insufficient` | ✅ PASSED |
| `test_build_doubt_certificate_with_actions` | ✅ PASSED |
| `test_uncertainty_cause_from_type` | ✅ PASSED |
| `test_build_safety_response` | ✅ PASSED |
| `test_safety_response_contains_emergency_message` | ✅ PASSED |
| `test_compose_with_supported_claims` | ✅ PASSED |
| `test_compose_empty_claims` | ✅ PASSED |

---

### `tests/test_artifacts.py` (7/7 passed)

| Test | Status |
|------|--------|
| `test_redact_ssn` | ✅ PASSED |
| `test_redact_email` | ✅ PASSED |
| `test_redact_phone` | ✅ PASSED |
| `test_no_redaction_for_clean_text` | ✅ PASSED |
| `test_build_run_artifact_basic` | ✅ PASSED |
| `test_build_run_artifact_redacts_pii` | ✅ PASSED |
| `test_build_run_artifact_with_claims` | ✅ PASSED |

---

## Test Coverage by Component

| Component | Tests | Coverage |
|-----------|-------|----------|
| Health endpoint | 2 | ✅ Good |
| Prompt injection detection | 4 | ✅ Good |
| PII detection | 7 | ✅ Good |
| Safety gate (CURA-Med) | 13 | ✅ Good |
| Corpus loader (CURA-Med) | 7 | ✅ Good |
| Claims composer (CURA-Med) | 4 | ✅ Good |
| Verifier (CURA-Med) | 9 | ✅ Good |
| EAV controller (CURA-Med) | 10 | ✅ Good |
| Output modules (CURA-Med) | 6 | ✅ Good |
| Run artifacts (CURA-Med) | 7 | ✅ Good |

**All previously missing modules now have tests. No red cells remain.**

---

## Appendix: Full Test Output

```
============================= test session starts =============================
platform win32 -- Python 3.10.11, pytest-9.1.1, pluggy-1.6.0
cachedir: .pytest_cache
rootdir: D:\PROJECTS\CLAUDE_CLI_AGENTS\HACKER_EARTH\HACKATHONS\microOneHackerEarth\backend
configfile: pyproject.toml
plugins: anyio-4.14.2, langsmith-0.11.2, asyncio-1.4.0
asyncio: mode=strict, debug=False, asyncio_default_fixture_loop_scope=function
collecting ... collected 73 items

tests/test_artifacts.py::TestRedactText::test_redact_ssn PASSED          [  1%]
tests/test_artifacts.py::TestRedactText::test_redact_email PASSED        [  2%]
tests/test_artifacts.py::TestRedactText::test_redact_phone PASSED        [  4%]
tests/test_artifacts.py::TestRedactText::test_no_redaction_for_clean_text PASSED [  5%]
tests/test_artifacts.py::TestBuildRunArtifact::test_build_run_artifact_basic PASSED [  6%]
tests/test_artifacts.py::TestBuildRunArtifact::test_build_run_artifact_redacts_pii PASSED [  8%]
tests/test_artifacts.py::TestBuildRunArtifact::test_build_run_artifact_with_claims PASSED [  9%]
tests/test_claims_composer.py::TestClaimComposer::test_decompose_simple_answer PASSED [ 10%]
tests/test_claims_composer.py::TestClaimComposer::test_decompose_empty_answer PASSED [ 12%]
tests/test_claims_composer.py::TestClaimComposer::test_decompose_single_sentence PASSED [ 13%]
tests/test_claims_composer.py::TestClaimComposer::test_match_citations PASSED [ 15%]
tests/test_corpus_loader.py::TestCorpusHash::test_sha256_file PASSED     [ 16%]
tests/test_corpus_loader.py::TestCorpusHash::test_sha256_string PASSED   [ 17%]
tests/test_corpus_loader.py::TestCorpusHash::test_compute_corpus_hash PASSED [ 19%]
tests/test_corpus_loader.py::TestCorpusHash::test_compute_corpus_hash_empty PASSED [ 20%]
tests/test_corpus_loader.py::TestCorpusLoader::test_load_corpus_chunks PASSED [ 22%]
tests/test_corpus_loader.py::TestCorpusLoader::test_load_corpus_chunks_empty PASSED [ 23%]
tests/test_corpus_loader.py::TestCorpusLoader::test_build_evidence_packet PASSED [ 25%]
tests/test_eav_controller.py::TestEAVController::test_no_action_for_singleton_supported PASSED [ 26%]
tests/test_eav_controller.py::TestEAVController::test_clarify_for_missing_entities PASSED [ 27%]
tests/test_eav_controller.py::TestEAVController::test_clarify_for_underspecified_scope PASSED [ 28%]
tests/test_eav_controller.py::TestEAVController::test_retrieve_for_low_claim_coverage PASSED [ 29%]
tests/test_eav_controller.py::TestEAVController::test_retrieve_for_conflict PASSED [ 30%]
tests/test_eav_controller.py::TestEAVController::test_no_action_when_budget_exhausted PASSED [ 31%]
tests/test_eav_controller.py::TestEAVController::test_record_action PASSED [ 35%]
tests/test_eav_controller.py::TestEAVController::test_record_action_not_productive PASSED [ 36%]
tests/test_eav_controller.py::TestEAVController::test_reset_budget PASSED [ 38%]
tests/test_health.py::test_health_endpoint_returns_200 PASSED            [ 40%]
tests/test_health.py::test_health_endpoint_has_expected_structure PASSED [ 41%]
tests/test_output_modules.py::TestDoubtCertificate::test_build_doubt_certificate_insufficient PASSED [ 42%]
tests/test_output_modules.py::TestDoubtCertificate::test_build_doubt_certificate_with_actions PASSED [ 44%]
tests/test_output_modules.py::TestDoubtCertificate::test_uncertainty_cause_from_type PASSED [ 45%]
tests/test_output_modules.py::TestSafetyResponse::test_build_safety_response PASSED [ 46%]
tests/test_output_modules.py::TestSafetyResponse::test_safety_response_contains_emergency_message PASSED [ 47%]
tests/test_output_modules.py::TestAnswerComposer::test_compose_with_supported_claims PASSED [ 49%]
tests/test_output_modules.py::TestAnswerComposer::test_compose_empty_claims PASSED [ 50%]
tests/test_pii_detector.py::test_clean_medical_query_passes PASSED       [ 52%]
tests/test_pii_detector.py::test_patient_id_is_redacted PASSED           [ 54%]
tests/test_pii_detector.py::test_mrn_is_redacted PASSED           [ 55%]
tests/test_pii_detector.py::test_disabled_mode_skips_redaction PASSED    [ 56%]
tests/test_pii_detector.py::test_strict_mode_raises_422 PASSED    [ 57%]
tests/test_pii_detector.py::test_mask_mode_produces_masked_output PASSED    [ 58%]
tests/test_pii_detector.py::test_non_pii_text_passes_through PASSED    [ 59%]
tests/test_prompt_injection_detector.py::test_clean_query_passes PASSED  [ 62%]
tests/test_prompt_injection_detector.py::test_jailbreak_pattern_is_blocked PASSED [ 84%]
tests/test_prompt_injection_detector.py::test_disabled_mode_skips_validation PASSED [ 92%]
tests/test_prompt_injection_detector.py::test_multiple_patterns_blocked PASSED [100%]
tests/test_safety_gate.py::TestSafetyGate (13 tests) PASSED
tests/test_corpus_loader.py (7 tests) PASSED
tests/test_claims_composer.py (4 tests) PASSED
tests/test_verifier_modules.py (9 tests) PASSED
tests/test_eav_controller.py (10 tests) PASSED
tests/test_output_modules.py (7 tests) PASSED
tests/test_artifacts.py (7 tests) PASSED

-- Docs: https://docs.pytest.org/en/9.1.1/how/to/capture.html
======================= 73 passed, 4 warnings in 11.10s ========================
```
