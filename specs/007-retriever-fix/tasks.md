# Tasks: 007-retriever-fix

**Feature**: 007-retriever-fix
**Branch**: `007-retriever-fix`
**Created**: 2026-09-08

## Task 1: Increase top_k in ask_question.py (Priority: P1)

**File**: `backend/server/routes/ask_question.py`
**Line**: 80

**Change**: 
```python
# Before:
top_k=2,  # Reduced from 3 to save tokens

# After:
top_k=5,  # Increased to capture more relevant evidence
```

**Why**: The current top_k=2 means the verifier never sees the 3rd-best chunk, even if it contains the correct answer. Increasing to top_k=5 gives the verifier a better chance of finding the evidence it needs.

**Test**: Run the comparative study and verify that the retriever returns 5 chunks per query instead of 2.

---

## Task 2: Remove 500-char truncation in ask_question.py (Priority: P1)

**File**: `backend/server/routes/ask_question.py`
**Lines**: 85, 119

**Change**:
```python
# Before (line 85):
page_content=match["metadata"].get("text", "")[:500],  # Truncate passages to save tokens

# After:
page_content=match["metadata"].get("text", ""),  # Preserve full passage text

# Before (line 119):
text=match["metadata"].get("text", "")[:500],  # Truncate to save tokens

# After:
text=match["metadata"].get("text", ""),  # Preserve full passage text
```

**Why**: The 500-character hard truncation silently removes evidence that appears after character 500. For medical passages, the specific fact needed to answer a question often appears later in the text.

**Test**: Verify that retrieved passages contain the full text from the corpus. Check that D1's "650 mg" answer is present in retrieved passages.

---

## Task 3: Remove 500-char truncation in medrag_baseline.py (Priority: P1)

**File**: `backend/server/routes/medrag_baseline.py`
**Line**: 70

**Change**:
```python
# Before:
page_content=match["metadata"].get("text", "")[:500],  # Truncate passages to save tokens

# After:
page_content=match["metadata"].get("text", ""),  # Preserve full passage text
```

**Why**: The MedRAG baseline should use the same retrieval quality as the main pipeline for fair comparison.

**Test**: Verify that MedRAG baseline returns full passage text.

---

## Task 4: Re-run comparative study (Priority: P2)

**Command**:
```bash
cd backend
source /tmp/microone_test/bin/activate
PYTHONPATH=/Users/mahedjaved/Desktop/APPS/Applications/Walmart/microOneHackerEarth python tests/comparative/run_all.py
```

**Expected outcome**: 
- 36 questions × 3 systems = 108 API calls
- Results saved to `tests/comparative/results/`
- Compare abstention rates and accuracy scores before/after

---

## Task 5: Generate updated performance report (Priority: P2)

**Command**:
```bash
source /tmp/microone_test/bin/activate
PYTHONPATH=/Users/mahedjaved/Desktop/APPS/Applications/Walmart/microOneHackerEarth python tests/comparative/generate_performance_report.py
```

**Expected outcome**: 
- `submission/performance_comparison.html` updated with new results
- Report clearly shows performance differences between NoRAG/MedRAG/UQ-RAG

---

## Task 6: Analyze retrieval-starvation vs. verifier-reasoning failures (Priority: P2)

**Analysis**:
1. Compare abstention rates before and after the fix
2. Identify questions that changed from "insufficient_evidence" to "supported" or "refuted"
3. Determine what percentage of the previous abstention rate was due to retrieval starvation

**Deliverable**: Add a section to `submission/performance_comparison.html` or create a new analysis document summarizing the findings.

---

## Task 7: Run backend unit tests (Priority: P3)

**Command**:
```bash
cd backend
python -m pytest tests/ -v --tb=short
```

**Expected outcome**: All 73 backend unit tests pass.
