# Feature Specification: timing-instrumentation

**Feature Branch**: `008-timing-instrumentation`

**Created**: 2026-09-09

**Status**: Draft

**Input**: User description: "Add timing instrumentation to identify why the comparative study run time is ~30 minutes. Instrument ask_question.py and run_study.py to log per-stage timing (Pinecone query, LLM generation, verifier/conformal) and rate-limit/retry events. Run a small subset (5 test cases) with top_k=5 and compare against top_k=2. Do not change retrieval logic or top_k values."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Instrument ask_question.py with per-stage timing (Priority: P1)

As a developer investigating pipeline latency, I want `ask_question.py` to log elapsed time for each major stage (Pinecone query, LLM generation, UQ pipeline/verifier) per request, so I can see where time is actually being spent.

**Why this priority**: Without per-stage timing, we cannot distinguish between retrieval latency, LLM latency, and verifier latency. The 30-minute run time could be caused by any of these, and the fix depends on which one is dominant.

**Independent Test**: Add `time.time()` start/end logging around each stage in `ask_question.py`, make a test request, and verify the logs show separate timing for Pinecone query, LLM generation, and UQ pipeline.

**Acceptance Scenarios**:

1. **Given** a request to `/ask/`, **When** the request completes, **Then** the logs contain three separate timing measurements: Pinecone query time, LLM generation time, and UQ pipeline time.
2. **Given** the instrumentation is active, **When** a request takes >10 seconds, **Then** the logs identify which stage caused the delay.
3. **Given** a rate-limit error occurs, **When** the error is caught, **Then** the log includes the retry count and backoff duration.

---

### User Story 2 - Instrument run_study.py with per-case timing and rate-limit detection (Priority: P1)

As a developer running the comparative study, I want `run_study.py` to log timestamps before/after each test case and explicitly flag rate-limit errors or retries, so I can correlate slow cases with API throttling.

**Why this priority**: The comparative study runs ~120 API calls (40 cases × 3 systems). If a fraction of these hit rate limits and trigger exponential backoff, the total run time can balloon from minutes to 30+ minutes. We need to detect this pattern.

**Independent Test**: Run the comparative study with instrumentation active and verify that each test case logs start/end timestamps, and any rate-limit responses are explicitly flagged with retry/backoff details.

**Acceptance Scenarios**:

1. **Given** the comparative study is running, **When** a test case completes, **Then** the output includes the elapsed time for that case.
2. **Given** an API returns a rate-limit error (HTTP 429), **When** the retry logic triggers, **Then** the log includes the retry attempt number and wait duration.
3. **Given** multiple test cases are run, **When** the study completes, **Then** the output includes a summary of total time, per-case times, and count of rate-limit events.

---

### User Story 3 - Run subset comparison: top_k=5 vs top_k=2 (Priority: P1)

As a developer, I want to run the same 5 test cases with both `top_k=5` and `top_k=2` to compare per-stage timing, so I can determine whether increased retrieval depth is the primary cause of slowdown.

**Why this priority**: The retriever fix changed `top_k` from 2 to 5. We need to isolate whether this change caused the runtime increase, or whether the runtime is dominated by LLM latency or rate-limiting.

**Independent Test**: Select 5 representative test cases from the accuracy suite (D1-D5). Run them with `top_k=5` (current) and `top_k=2` (previous) with instrumentation active. Compare per-stage timing.

**Acceptance Scenarios**:

1. **Given** 5 test cases are selected, **When** run with `top_k=5`, **Then** per-stage timing is recorded for each case.
2. **Given** the same 5 test cases, **When** run with `top_k=2`, **Then** per-stage timing is recorded for each case.
3. **Given** both runs complete, **When** the timing data is compared, **Then** we can identify which stage(s) scale with `top_k` and which do not.

---

### User Story 4 - Generate timing report with raw per-stage data (Priority: P2)

As a developer, I want a structured timing report (JSON or Markdown) containing raw per-stage timing for each test case, so I can analyze the data without parsing log files.

**Why this priority**: Raw log parsing is error-prone. A structured report makes it easy to identify patterns across test cases and stages.

**Independent Test**: After running the subset comparison, verify that a timing report file is generated with per-case, per-stage timing data.

**Acceptance Scenarios**:

1. **Given** the instrumentation run completes, **When** the report is generated, **Then** it contains entries for each test case with Pinecone time, LLM time, UQ pipeline time, and total time.
2. **Given** rate-limit events occurred, **When** the report is generated, **Then** it includes a summary of rate-limit count, total retry time, and affected cases.
3. **Given** both `top_k=5` and `top_k=2` runs complete, **When** the report is generated, **Then** it includes a comparison section showing delta per stage.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `backend/server/routes/ask_question.py` MUST log `time.time()` start/end timestamps for: Pinecone query, LLM generation (`llm_chain.invoke`), and UQ pipeline (`run_uq_pipeline`).
- **FR-002**: `backend/server/routes/ask_question.py` MUST log rate-limit errors and retry attempts with elapsed backoff time.
- **FR-003**: `tests/comparative/run_study.py` MUST log a timestamp before and after each individual test case, and compute per-case elapsed time.
- **FR-004**: `tests/comparative/run_study.py` MUST explicitly flag HTTP 429 responses and log retry/backoff details.
- **FR-005**: A timing report file MUST be generated after the instrumentation run, containing raw per-stage timing data in JSON format.
- **FR-006**: The instrumentation MUST NOT change `top_k`, truncation limits, or any retrieval logic.
- **FR-007**: The instrumentation MUST be additive only — no existing behavior or return values may be altered.

### Key Entities *(include if feature involves data)*

- **TimingReport**: JSON structure containing per-case timing data, rate-limit events, and comparison between top_k configurations.
- **StageTiming**: Named tuple or dict with fields: `stage_name`, `start_time`, `end_time`, `elapsed_ms`.
- **RateLimitEvent**: Dict with fields: `test_case_id`, `endpoint`, `attempt`, `backoff_seconds`, `http_status`.

## Success Criteria *(mandatory)

### Measurable Outcomes

- **SC-001**: `ask_question.py` logs contain three separate timing measurements per request (Pinecone, LLM, UQ pipeline).
- **SC-002**: `run_study.py` logs contain per-case elapsed times and explicit rate-limit/retry flags.
- **SC-003**: A timing report JSON file is generated with raw per-stage data for at least 5 test cases.
- **SC-004**: The timing report includes a comparison between `top_k=5` and `top_k=2` runs, identifying which stage(s) scale with retrieval depth.
- **SC-005**: The instrumentation does not alter any pipeline logic, return values, or test scores.

## Assumptions

- The 30-minute run time is caused by either LLM latency, rate-limit backoff, or sequential execution — not by the RandomForest classifier itself.
- Adding `time.time()` logging has negligible performance impact (<1% overhead).
- The comparative study harness (`run_study.py`) can be modified to add timing without breaking existing result file generation.
- Running 5 test cases is sufficient to identify scaling patterns; full 36-case run is not required for this investigation.
- Rate-limit errors, if present, will be detectable from HTTP status codes or exception messages in the existing retry logic.
