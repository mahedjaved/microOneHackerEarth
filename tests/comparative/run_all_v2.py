"""
Run all comparative tests for v2 scoring system.
Multiple runs with delays for rate limit handling.
"""

import os
import json
import time
import requests
from datetime import datetime

from tests.comparative.test_dataset_v2 import TEST_QUESTIONS
from tests.comparative.scoring_v2 import score_response, compute_aggregate_metrics

BACKEND_URL = "http://127.0.0.1:8000"

ENDPOINTS = {
    "uq_rag": f"{BACKEND_URL}/ask/",
    "medrag_baseline": f"{BACKEND_URL}/medrag_baseline/",
    "no_rag": f"{BACKEND_URL}/no_rag/",
}

REQUEST_DELAY = 2  # seconds between requests
NUM_RUNS = 3
MAX_RETRIES = 3
RETRY_BACKOFF = 5  # seconds base for exponential backoff


def ask_system(endpoint, question, timeout=60):
    """
    Send question to a system with retry-with-backoff for rate limits.

    Retries on HTTP 429 (rate limit) and 5xx (server error).
    Exponential backoff: 5s, 10s, 20s between retries.
    """
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(endpoint, data={"question": question}, timeout=timeout)

            # Success
            if response.status_code == 200:
                return response

            # Rate limited - retry with backoff
            if response.status_code == 429:
                wait_time = RETRY_BACKOFF * (2 ** attempt)
                print(f"    Rate limited (429), retrying in {wait_time}s (attempt {attempt + 1}/{MAX_RETRIES})...")
                time.sleep(wait_time)
                continue

            # Server error - retry with backoff
            if response.status_code >= 500:
                wait_time = RETRY_BACKOFF * (2 ** attempt)
                print(f"    Server error ({response.status_code}), retrying in {wait_time}s (attempt {attempt + 1}/{MAX_RETRIES})...")
                time.sleep(wait_time)
                continue

            # Other error - return response (will be handled by caller)
            return response

        except requests.exceptions.Timeout:
            wait_time = RETRY_BACKOFF * (2 ** attempt)
            print(f"    Timeout, retrying in {wait_time}s (attempt {attempt + 1}/{MAX_RETRIES})...")
            if attempt < MAX_RETRIES - 1:
                time.sleep(wait_time)
                continue
            raise

        except requests.exceptions.ConnectionError:
            wait_time = RETRY_BACKOFF * (2 ** attempt)
            print(f"    Connection error, retrying in {wait_time}s (attempt {attempt + 1}/{MAX_RETRIES})...")
            if attempt < MAX_RETRIES - 1:
                time.sleep(wait_time)
                continue
            raise

    # All retries exhausted
    return response


def run_single_iteration(iteration):
    """Run one complete test iteration."""
    results = []
    error_count = 0

    for test_case in TEST_QUESTIONS:
        q_id = test_case["id"]
        question = test_case["question"]
        print(f"  [{iteration}] Testing {q_id}: {question[:50]}...")

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
                    # Preserve original API response for debugging
                    question_result["scores"][system_name] = {
                        "api_response": data,
                        "timestamp": datetime.now().isoformat()
                    }
                    # Score in separate try/except to preserve API data on scoring failure
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
                    question_result["scores"][system_name] = {
                        "score": 0.0,
                        "error": f"HTTP {response.status_code}",
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
        print(f"  [{iteration}] {error_count} errors encountered (excluded from behavioral averages)")

    return results


def run_all_iterations():
    """Run all test iterations and compute aggregates."""
    os.makedirs("tests/comparative/results", exist_ok=True)
    
    all_run_results = []
    
    for run_idx in range(1, NUM_RUNS + 1):
        print(f"\n=== Run {run_idx}/{NUM_RUNS} ===")
        run_results = run_single_iteration(run_idx)
        all_run_results.append(run_results)
        
        # Save per-run results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_file = f"tests/comparative/results/run{run_idx}_{timestamp}.json"
        with open(run_file, "w") as f:
            json.dump(run_results, f, indent=2)
    
    # Compute aggregate metrics
    print("\n=== Computing Aggregate Metrics ===")
    aggregates = compute_all_aggregates(all_run_results)
    
    # Save summary
    with open("tests/comparative/results/summary.json", "w") as f:
        json.dump(aggregates, f, indent=2)
    
    # Print summary
    print("\n=== RESULTS SUMMARY ===")
    for system_name, metrics in aggregates["systems"].items():
        error_info = f", errors: {metrics['errors']}/{metrics['total_questions']} ({metrics['error_rate']:.0%})" if metrics.get('errors', 0) > 0 else ""
        print(f"{system_name}: {metrics['mean']:.3f} ± {metrics['std']:.3f} (95% CI: {metrics['ci_95']}){error_info}")

    winner = max(aggregates["systems"].items(), key=lambda x: x[1]["mean"])
    print(f"\nWinner: {winner[0]} (score: {winner[1]['mean']:.3f})")

    return aggregates


def compute_all_aggregates(all_run_results):
    """Compute aggregate metrics across all runs. Excludes errored results from behavioral averages."""
    systems = ["uq_rag", "medrag_baseline", "no_rag"]

    aggregates = {"systems": {}, "runs": len(all_run_results)}

    for system_name in systems:
        # Collect scores per dimension (excluding errors)
        all_scores = []
        dimension_scores = {"accuracy": [], "safety": [], "calibration": [], "hallucination": []}
        error_count = 0
        total_count = 0

        for run_results in all_run_results:
            for q_result in run_results:
                score_data = q_result["scores"].get(system_name, {})
                total_count += 1

                # Skip errored results in behavioral averages
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
            "std": compute_std(all_scores),
            "ci_95": compute_ci(all_scores),
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


def compute_std(values):
    """Compute standard deviation."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return variance ** 0.5


def compute_ci(values):
    """Compute 95% confidence interval."""
    if len(values) < 2:
        return [0.0, 0.0]
    mean = sum(values) / len(values)
    std = compute_std(values)
    se = std / (len(values) ** 0.5)
    return [max(0.0, mean - 1.96 * se), min(1.0, mean + 1.96 * se)]


if __name__ == "__main__":
    run_all_iterations()
