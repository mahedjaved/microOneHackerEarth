"""
Master script to run UQ-RAG comparative study with enhanced analysis.

Usage:
    python tests/comparative/run_study.py

This will:
1. Run the comparative study (if backend is available)
2. Generate analysis plots
3. Generate HTML report
"""

import os
import sys
import time
import json
import requests
from datetime import datetime
from pathlib import Path

# Add tests directory to path
sys.path.insert(0, os.path.dirname(__file__))

from test_dataset_enhanced import ALL_QUESTIONS, get_questions_by_suite
from scoring_v2 import score_response, compute_aggregate_metrics


BACKEND_URL = "http://127.0.0.1:8000"
ENDPOINTS = {
    "uq_rag": f"{BACKEND_URL}/ask/",
    "medrag_baseline": f"{BACKEND_URL}/medrag_baseline/",
    "no_rag": f"{BACKEND_URL}/no_rag/",
}
REQUEST_DELAY = 5  # seconds between requests (increased to avoid rate limiting)
NUM_RUNS = 1  # Reduced from 3 to save tokens while stabilizing
MAX_RETRIES = 3
RETRY_BACKOFF = 10  # Increased backoff for rate limits


def check_backend() -> bool:
    """Check if backend is running."""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def ask_system(endpoint: str, question: str, timeout: int = 90):
    """Send question to a system with retry-with-backoff."""
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(endpoint, data={"question": question}, timeout=timeout)

            if response.status_code == 200:
                return response

            if response.status_code == 429:
                wait_time = RETRY_BACKOFF * (2 ** attempt)
                print(f"    Rate limited (429), retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue

            if response.status_code >= 500:
                wait_time = RETRY_BACKOFF * (2 ** attempt)
                # Capture error detail for debugging
                try:
                    error_detail = response.text[:200]
                except:
                    error_detail = "Could not read response body"
                print(f"    Server error ({response.status_code}), retrying in {wait_time}s...")
                print(f"    Error detail: {error_detail}")
                time.sleep(wait_time)
                continue

            return response

        except requests.exceptions.Timeout:
            wait_time = RETRY_BACKOFF * (2 ** attempt)
            print(f"    Timeout, retrying in {wait_time}s...")
            if attempt < MAX_RETRIES - 1:
                time.sleep(wait_time)
                continue
            raise

        except requests.exceptions.ConnectionError:
            wait_time = RETRY_BACKOFF * (2 ** attempt)
            print(f"    Connection error, retrying in {wait_time}s...")
            if attempt < MAX_RETRIES - 1:
                time.sleep(wait_time)
                continue
            raise

    return response


def run_single_iteration(iteration: int, questions: list):
    """Run one complete test iteration."""
    results = []
    error_count = 0

    for test_case in questions:
        q_id = test_case["id"]
        question = test_case["question"]
        print(f"  [{iteration}] Testing {q_id}: {question[:60]}...")

        question_result = {
            "test_case": test_case,
            "scores": {},
            "timestamp": datetime.now().isoformat()
        }

        for system_name, endpoint in ENDPOINTS.items():
            try:
                time.sleep(REQUEST_DELAY)
                response = ask_system(endpoint, question)

                if response.status_code == 200:
                    data = response.json()
                    question_result["scores"][system_name] = {
                        "api_response": data,
                        "timestamp": datetime.now().isoformat()
                    }
                    try:
                        score_result = score_response(test_case, data, system_name)
                        question_result["scores"][system_name].update(score_result)
                    except Exception as score_err:
                        question_result["scores"][system_name].update({
                            "score": 0.0,
                            "error": f"Scoring error: {str(score_err)}",
                            "errored": True,
                            "timestamp": datetime.now().isoformat()
                        })
                        error_count += 1
                else:
                    # Capture actual response body for debugging
                    try:
                        error_body = response.text[:300]
                    except:
                        error_body = "Could not read response body"
                    question_result["scores"][system_name] = {
                        "score": 0.0,
                        "error": f"HTTP {response.status_code}",
                        "error_detail": error_body,
                        "errored": True,
                        "timestamp": datetime.now().isoformat()
                    }
                    error_count += 1
            except Exception as e:
                question_result["scores"][system_name] = {
                    "score": 0.0,
                    "error": str(e),
                    "errored": True,
                    "timestamp": datetime.now().isoformat()
                }
                error_count += 1

        results.append(question_result)

    if error_count > 0:
        print(f"  [{iteration}] {error_count} errors (excluded from behavioral averages)")

    return results


def compute_all_aggregates(all_run_results):
    """Compute aggregate metrics across all runs."""
    systems = ["uq_rag", "medrag_baseline", "no_rag"]

    aggregates = {"systems": {}, "runs": len(all_run_results)}

    for system_name in systems:
        all_scores = []
        dimension_scores = {"accuracy": [], "safety": [], "calibration": [], "hallucination": []}
        error_count = 0
        total_count = 0

        for run_results in all_run_results:
            for q_result in run_results:
                score_data = q_result["scores"].get(system_name, {})
                total_count += 1

                if score_data.get("errored"):
                    error_count += 1
                    continue

                score = score_data.get("score", 0)
                dimension = score_data.get("dimension", "unknown")

                all_scores.append(score)
                if dimension in dimension_scores:
                    dimension_scores[dimension].append(score)

        aggregates["systems"][system_name] = {
            "mean": sum(all_scores) / len(all_scores) if all_scores else 0,
            "std": (sum((x - sum(all_scores)/len(all_scores))**2 for x in all_scores) / (len(all_scores)-1))**0.5 if len(all_scores) > 1 else 0,
            "n": len(all_scores),
            "total_questions": total_count,
            "errors": error_count,
            "error_rate": error_count / total_count if total_count > 0 else 0,
            "dimensions": {
                dim: compute_aggregate_metrics(scores)
                for dim, scores in dimension_scores.items() if scores
            }
        }

    return aggregates


def archive_existing_runs():
    """Archive existing run files before starting a new study.

    Prevents stale data from blending with new results.
    """
    results_dir = Path("tests/comparative/results")
    archive_dir = results_dir / "archive"

    run_files = list(results_dir.glob("run*.json"))
    if not run_files:
        return

    archive_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for f in run_files:
        dest = archive_dir / f"{f.stem}_archived_{timestamp}{f.suffix}"
        f.rename(dest)
        print(f"  Archived: {f.name} -> archive/{dest.name}")

    # Also archive summary if present
    summary_file = results_dir / "summary.json"
    if summary_file.exists():
        dest = archive_dir / f"summary_archived_{timestamp}.json"
        summary_file.rename(dest)
        print(f"  Archived: summary.json -> archive/{dest.name}")


def run_study(suite: str = "original"):
    """Run the full comparative study."""
    print(f"=== UQ-RAG Comparative Study ===")
    print(f"Suite: {suite}")
    print(f"Runs: {NUM_RUNS}")
    print(f"Questions per run: {len(get_questions_by_suite(suite))}")
    print()

    if not check_backend():
        print(f"ERROR: Backend not available at {BACKEND_URL}")
        print("Start the backend first: cd backend && python -m uvicorn server.main:app --reload")
        return None

    # Archive existing runs to prevent stale data contamination
    print("Archiving previous run files...")
    archive_existing_runs()

    questions = get_questions_by_suite(suite)
    all_run_results = []

    for run_idx in range(1, NUM_RUNS + 1):
        print(f"\n=== Run {run_idx}/{NUM_RUNS} ===")
        run_results = run_single_iteration(run_idx, questions)
        all_run_results.append(run_results)

        # Save per-run results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = Path("tests/comparative/results")
        results_dir.mkdir(parents=True, exist_ok=True)
        run_file = results_dir / f"run{run_idx}_{timestamp}.json"
        with open(run_file, "w") as f:
            json.dump(run_results, f, indent=2)

    # Compute aggregates
    print("\n=== Computing Aggregate Metrics ===")
    aggregates = compute_all_aggregates(all_run_results)

    # Save summary
    with open("tests/comparative/results/summary.json", "w") as f:
        json.dump(aggregates, f, indent=2)

    # Print summary
    print("\n=== RESULTS SUMMARY ===")
    for system_name, metrics in aggregates["systems"].items():
        error_info = f", errors: {metrics['errors']}/{metrics['total_questions']}" if metrics.get('errors', 0) > 0 else ""
        print(f"{system_name}: {metrics['mean']:.3f} ± {metrics['std']:.3f}{error_info}")

    winner = max(aggregates["systems"].items(), key=lambda x: x[1]["mean"])
    print(f"\nWinner: {winner[0]} (score: {winner[1]['mean']:.3f})")

    return aggregates


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run UQ-RAG comparative study")
    parser.add_argument("--suite", default="original",
                       choices=["original", "accuracy", "safety", "calibration", "hallucination", "adversarial", "uq_paper", "all"],
                       help="Test suite to run")
    args = parser.parse_args()

    run_study(args.suite)
