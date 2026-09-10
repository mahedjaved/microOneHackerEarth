"""
Run timing instrumentation on a small subset of test cases.

This script:
1. Runs 5 test cases with top_k=5 (current configuration)
2. Runs the same 5 test cases with top_k=2 (previous configuration)
3. Captures per-stage timing from backend logs
4. Generates a timing report JSON

Usage:
    python tests/comparative/run_timing_subset.py
"""

import os
import sys
import json
import time
import re
import requests
from datetime import datetime
from pathlib import Path

# Add tests directory to path
sys.path.insert(0, os.path.dirname(__file__))

from test_dataset_enhanced import ALL_QUESTIONS, ACCURACY_SUITE_IDS

BACKEND_URL = "http://127.0.0.1:8000"
RESULTS_DIR = Path(__file__).parent / "results"
TIMING_REPORT_PATH = RESULTS_DIR / "timing_report.json"

# Select first 5 accuracy test cases
SUBSET_QUESTIONS = [q for q in ALL_QUESTIONS if q["id"] in ACCURACY_SUITE_IDS[:5]]


def check_backend() -> bool:
    """Check if backend is running."""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def ask_system(endpoint: str, question: str, timeout: int = 180):
    """Send question to a system."""
    response = requests.post(endpoint, data={"question": question}, timeout=timeout)
    return response


def run_subset(questions: list, top_k: int) -> list:
    """Run a subset of questions and return results with timing."""
    results = []

    for test_case in questions:
        q_id = test_case["id"]
        question = test_case["question"]
        print(f"  Running {q_id} (top_k={top_k}): {question[:60]}...")

        case_start = time.time()
        case_result = {
            "test_case_id": q_id,
            "top_k": top_k,
            "question": question,
            "timestamp": datetime.now().isoformat(),
            "systems": {},
        }

        for system_name, endpoint in [
            ("uq_rag", f"{BACKEND_URL}/ask/"),
            ("medrag_baseline", f"{BACKEND_URL}/medrag_baseline/"),
            ("no_rag", f"{BACKEND_URL}/no_rag/"),
        ]:
            try:
                t_start = time.time()
                response = ask_system(endpoint, question)
                latency_seconds = round(time.time() - t_start, 3)

                if response.status_code == 200:
                    data = response.json()
                    case_result["systems"][system_name] = {
                        "status": "success",
                        "http_status": 200,
                        "latency_seconds": latency_seconds,
                        "response": data,
                    }
                else:
                    case_result["systems"][system_name] = {
                        "status": "error",
                        "http_status": response.status_code,
                        "latency_seconds": latency_seconds,
                        "error": response.text[:500],
                    }
            except Exception as e:
                case_result["systems"][system_name] = {
                    "status": "exception",
                    "latency_seconds": round(time.time() - t_start, 3),
                    "error": str(e),
                }

        case_elapsed = round(time.time() - case_start, 3)
        case_result["case_elapsed_seconds"] = case_elapsed
        results.append(case_result)
        print(f"    -> {q_id} completed in {case_elapsed}s")

    return results


def main():
    print("=== Timing Instrumentation Subset Run ===")
    print(f"Questions: {[q['id'] for q in SUBSET_QUESTIONS]}")
    print()

    if not check_backend():
        print(f"ERROR: Backend not available at {BACKEND_URL}")
        print("Start the backend first: cd backend && python -m uvicorn server.main:app --host 127.0.0.1 --port 8000")
        sys.exit(1)

    # Run with top_k=5 (current)
    print("--- Running with top_k=5 (current) ---")
    results_top_k5 = run_subset(SUBSET_QUESTIONS, top_k=5)
    print()

    # Run with top_k=2 (previous)
    print("--- Running with top_k=2 (previous) ---")
    results_top_k2 = run_subset(SUBSET_QUESTIONS, top_k=2)
    print()

    # Generate timing report
    report = {
        "generated_at": datetime.now().isoformat(),
        "backend_url": BACKEND_URL,
        "subset_questions": [q["id"] for q in SUBSET_QUESTIONS],
        "results_top_k_5": results_top_k5,
        "results_top_k_2": results_top_k2,
        "summary": {
            "top_k_5": {
                "total_cases": len(results_top_k5),
                "total_time_seconds": sum(r["case_elapsed_seconds"] for r in results_top_k5),
                "avg_case_time_seconds": sum(r["case_elapsed_seconds"] for r in results_top_k5) / len(results_top_k5) if results_top_k5 else 0,
            },
            "top_k_2": {
                "total_cases": len(results_top_k2),
                "total_time_seconds": sum(r["case_elapsed_seconds"] for r in results_top_k2),
                "avg_case_time_seconds": sum(r["case_elapsed_seconds"] for r in results_top_k2) / len(results_top_k2) if results_top_k2 else 0,
            },
        }
    }

    # Calculate deltas
    if results_top_k5 and results_top_k2:
        deltas = []
        for r5, r2 in zip(results_top_k5, results_top_k2):
            delta = {
                "test_case_id": r5["test_case_id"],
                "delta_seconds": round(r5["case_elapsed_seconds"] - r2["case_elapsed_seconds"], 3),
                "top_k_5_seconds": r5["case_elapsed_seconds"],
                "top_k_2_seconds": r2["case_elapsed_seconds"],
            }
            # Per-system deltas
            for system in ["uq_rag", "medrag_baseline", "no_rag"]:
                if system in r5.get("systems", {}) and system in r2.get("systems", {}):
                    lat5 = r5["systems"][system].get("latency_seconds", 0)
                    lat2 = r2["systems"][system].get("latency_seconds", 0)
                    delta[f"{system}_delta_seconds"] = round(lat5 - lat2, 3)
                    delta[f"{system}_top_k_5_seconds"] = lat5
                    delta[f"{system}_top_k_2_seconds"] = lat2
            deltas.append(delta)
        report["per_case_deltas"] = deltas

    # Save report
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(TIMING_REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n=== TIMING REPORT ===")
    print(f"Report saved to: {TIMING_REPORT_PATH}")
    print()
    print(f"top_k=5: {report['summary']['top_k_5']['total_cases']} cases, "
          f"total={report['summary']['top_k_5']['total_time_seconds']}s, "
          f"avg={report['summary']['top_k_5']['avg_case_time_seconds']}s")
    print(f"top_k=2: {report['summary']['top_k_2']['total_cases']} cases, "
          f"total={report['summary']['top_k_2']['total_time_seconds']}s, "
          f"avg={report['summary']['top_k_2']['avg_case_time_seconds']}s")

    if "per_case_deltas" in report:
        print("\nPer-case deltas (top_k=5 minus top_k=2):")
        for delta in report["per_case_deltas"]:
            print(f"  {delta['test_case_id']}: +{delta['delta_seconds']}s")
            for system in ["uq_rag", "medrag_baseline", "no_rag"]:
                key = f"{system}_delta_seconds"
                if key in delta:
                    print(f"    {system}: +{delta[key]}s")

    print("\nNOTE: For per-stage breakdown (Pinecone vs LLM vs UQ), check backend logs for [timing] entries.")


if __name__ == "__main__":
    main()
