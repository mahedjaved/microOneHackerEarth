# Quickstart: CURA-Med Frontend

**Feature**: 002-frontend-material  
**Date**: 2026-08-29  
**Status**: Draft

## Prerequisites

- Python 3.10+
- Backend server running at `http://127.0.0.1:8000`
- Frontend dependencies installed

## Setup

```powershell
# 1. Install frontend dependencies
cd frontend
pip install -r requirements.txt

# 2. Configure backend URL (optional)
# Set API_URL in config.py or environment variable
$env:API_URL = "http://127.0.0.1:8000"

# 3. Start backend (if not already running)
cd backend
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000
```

## Running the Frontend

```powershell
cd frontend
streamlit run app.py
```

The frontend opens at `http://127.0.0.1:8501`.

## Validation Scenarios

### Scenario 1: Upload and Question (P1)

**Steps**:
1. Open `http://127.0.0.1:8501`
2. Upload a valid PDF file using the upload component
3. Wait for upload confirmation
4. Ask: "What is aspirin used for?"
5. Verify response includes cited answer and sources
6. Verify medical disclaimer is shown

**Expected outcome**: Answer displayed with sources and disclaimer within 30 seconds.

---

### Scenario 2: Doubt Certificate (P2)

**Steps**:
1. Ask a question with no matching evidence in the corpus: "What is the cure for fictional disease X?"
2. Verify system displays a doubt certificate
3. Verify doubt certificate includes `status: insufficient_evidence`
4. Verify no confident answer is shown

**Expected outcome**: Doubt certificate displayed instead of a guess.

---

### Scenario 3: Emergency Response (P1)

**Steps**:
1. Ask: "I have severe chest pain and can't breathe"
2. Verify system responds within 2 seconds
3. Verify response directs user to emergency services
4. Verify no doubt certificate is shown

**Expected outcome**: Emergency response displayed within 2 seconds.

---

### Scenario 4: Conversation History (P2)

**Steps**:
1. Ask Question 1: "What is aspirin used for?"
2. Ask Question 2: "What are the side effects?"
3. Verify both questions and answers appear in chat history
4. Verify sources are shown for each answer
5. Refresh the page
6. Verify conversation history is cleared (session-only)

**Expected outcome**: Full conversation visible in session; cleared on refresh.

---

### Scenario 5: Download Run Artifact (P3)

**Steps**:
1. Ask a question and receive an answer
2. Note the `run_artifact_id` from the response
3. Click "Download Run Artifact" (or use backend API to fetch artifact)
4. Verify downloaded artifact contains question, answer, sources, and metadata
5. Verify PII is redacted in the artifact

**Expected outcome**: Artifact downloaded in under 5 seconds with all required fields.

---

### Scenario 6: Backend Unavailable (P2)

**Steps**:
1. Stop the backend server
2. Refresh the frontend page
3. Ask a question
4. Verify user-friendly error message is displayed
5. Restart backend
6. Ask a question again
7. Verify system recovers

**Expected outcome**: Clear error message when backend is down; automatic recovery when backend returns.

---

### Scenario 7: Non-PDF Upload (P2)

**Steps**:
1. Try to upload a non-PDF file (e.g., `.txt`, `.jpg`)
2. Verify system rejects the file with a clear error message
3. Verify upload button remains functional

**Expected outcome**: Non-PDF files rejected with clear feedback.

---

### Scenario 8: UAT Script (P2)

**Steps**:
1. Ensure backend and frontend are running
2. Run: `python frontend/uat_test.py`
3. Verify all test cases pass

**Expected outcome**: All UAT tests pass.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Backend not available" | Ensure backend is running at configured `API_URL` |
| "PII detection unavailable" | Install `presidio-analyzer`, `presidio-anonymizer`, `spacy` |
| Upload fails with 413 | Reduce file size to under 50MB |
| Emergency response slow | Check backend logs; emergency detection runs in backend |
| Chat history not persisting | Session state is cleared on page refresh; this is expected |

## Next Steps

After validation, proceed to:
- `/speckit.tasks` — break into implementation tasks
- `/speckit.implement` — execute the build
