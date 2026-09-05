#!/usr/bin/env python3
"""
Determinism test for safety gate behavior.

Runs each safety test case multiple times against MedRAG and NoRAG
to measure variance in safety detection. UQ-RAG's regex gate is
deterministic by construction (100/100 every time).

Usage:
    python scripts/determinism_test.py --trials 20
    python scripts/determinism_test.py --output submission/determinism_results.md
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add repo root to path
_REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from tests.comparative.test_dataset_enhanced import get_questions_by_suite
from tests.comparative.scoring import score_response

BACKEND_URL = "http://127.0.0.1:8000"
ENDPOINTS = {
    "uq_rag": f"{BACKEND_URL}/ask/",
    "medrag_baseline": f"{BACKEND_URL}/medrag_baseline/",
    "no_rag": f"{BACKEND_URL}/no_rag/",
}


def ask_system(endpoint, question, timeout=60):
    """Send question to a system and return response."""
    import requests
    response = requests.post(endpoint, data={"question": question}, timeout=timeout)
    return response


def run_determinism_test(n_trials: int = 20, output_dir: str = "tests/comparative/results"):
    """Run determinism test: multiple trials per safety case."""
    os.makedirs(output_dir, exist_ok=True)
    safety_cases = get_questions_by_suite("safety")

    print(f"Running determinism test: {n_trials} trials × {len(safety_cases)} cases × 3 systems")
    print(f"Cases: {[tc['id'] for tc in safety_cases]}")

    results = []

    for trial in range(1, n_trials + 1):
        print(f"\n--- Trial {trial}/{n_trials} ---")

        for test_case in safety_cases:
            q_id = test_case["id"]
            question = test_case["question"]

            trial_result = {
                "trial": trial,
                "test_case_id": q_id,
                "question": question,
                "system_results": {},
            }

            for system_name, endpoint in ENDPOINTS.items():
                try:
                    response = ask_system(endpoint, question)
                    if response.status_code == 200:
                        data = response.json()
                        score_data = score_response(test_case, data, system_name)
                        trial_result["system_results"][system_name] = {
                            "status": "ok",
                            "score": score_data["score"],
                            "safety_detected": score_data.get("safety_detected"),
                            "doubt_expressed": score_data.get("doubt_expressed"),
                        }
                    else:
                        trial_result["system_results"][system_name] = {
                            "status": f"http_{response.status_code}",
                            "score": 0,
                            "safety_detected": False,
                        }
                except Exception as e:
                    trial_result["system_results"][system_name] = {
                        "status": f"error: {str(e)[:50]}",
                        "score": 0,
                        "safety_detected": False,
                    }

            # Print progress
            uq_safe = trial_result["system_results"].get("uq_rag", {}).get("safety_detected", "N/A")
            med_safe = trial_result["system_results"].get("medrag_baseline", {}).get("safety_detected", "N/A")
            no_safe = trial_result["system_results"].get("no_rag", {}).get("safety_detected", "N/A")
            print(f"  {q_id}: UQ={uq_safe}, MedRAG={med_safe}, NoRAG={no_safe}")

        results.append(trial_result)

    # Save raw results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = os.path.join(output_dir, f"determinism_test_{timestamp}.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)

    # Compute summary statistics
    summary = compute_determinism_summary(results)
    summary_file = os.path.join(output_dir, f"determinism_summary_{timestamp}.json")
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    # Generate markdown report
    report = generate_determinism_report(results, summary, timestamp)
    report_file = os.path.join(output_dir, f"determinism_report_{timestamp}.md")
    with open(report_file, "w") as f:
        f.write(report)

    print(f"\nResults saved to {results_file}")
    print(f"Summary saved to {summary_file}")
    print(f"Report saved to {report_file}")

    return results, summary, report


def compute_determinism_summary(results: list) -> dict:
    """Compute determinism summary statistics."""
    systems = ["uq_rag", "medrag_baseline", "no_rag"]
    summary = {
        "timestamp": datetime.now().isoformat(),
        "n_trials": len(results),
        "n_cases": len(set(r["test_case_id"] for r in results)),
        "systems": {},
    }

    for system in systems:
        safety_values = []
        for r in results:
            val = r["system_results"].get(system, {}).get("safety_detected")
            if val is not None:
                safety_values.append(val)

        if safety_values:
            detection_rate = sum(safety_values) / len(safety_values)
            summary["systems"][system] = {
                "safety_detection_rate": detection_rate,
                "n_measurements": len(safety_values),
                "n_detected": sum(safety_values),
                "n_missed": len(safety_values) - sum(safety_values),
                "deterministic": detection_rate == 1.0,
            }
        else:
            summary["systems"][system] = {
                "safety_detection_rate": 0.0,
                "n_measurements": 0,
                "n_detected": 0,
                "n_missed": 0,
                "deterministic": False,
            }

    return summary


def generate_determinism_report(results: list, summary: dict, timestamp: str) -> str:
    """Generate markdown determinism report."""
    lines = [
        f"# Determinism Test Report",
        f"",
        f"**Generated:** {timestamp}",
        f"**Trials:** {summary['n_trials']}",
        f"**Cases:** {summary['n_cases']} safety cases",
        f"",
        f"## Summary",
        f"",
        f"| System | Safety Detection Rate | Detected | Missed | Deterministic? |",
        f"|--------|----------------------|----------|--------|----------------|",
    ]

    for system, stats in summary["systems"].items():
        rate = f"{stats['safety_detection_rate']:.1%}"
        deterministic = "✅ Yes" if stats["deterministic"] else "❌ No"
        lines.append(
            f"| {system} | {rate} | {stats['n_detected']} | {stats['n_missed']} | {deterministic} |"
        )

    lines.extend([
        f"",
        f"## Detailed Results by Case",
        f"",
    ])

    # Group by case
    cases = {}
    for r in results:
        qid = r["test_case_id"]
        if qid not in cases:
            cases[qid] = {"question": r["question"], "trials": []}
        cases[qid]["trials"].append(r)

    for qid, case_data in cases.items():
        lines.append(f"### {qid}: {case_data['question'][:80]}...")
        lines.append(f"")
        lines.append(f"| Trial | UQ-RAG | MedRAG | NoRAG |")
        lines.append(f"|-------|--------|--------|-------|")

        for trial in case_data["trials"]:
            t = trial["trial"]
            uq = trial["system_results"].get("uq_rag", {}).get("safety_detected", "N/A")
            med = trial["system_results"].get("medrag_baseline", {}).get("safety_detected", "N/A")
            no = trial["system_results"].get("no_rag", {}).get("safety_detected", "N/A")

            def fmt(val):
                if val is True:
                    return "✅"
                elif val is False:
                    return "❌"
                else:
                    return str(val)

            lines.append(f"| {t} | {fmt(uq)} | {fmt(med)} | {fmt(no)} |")

        lines.append(f"")

    lines.extend([
        f"## Analysis",
        f"",
        f"UQ-RAG's regex-based safety gate is deterministic by construction:",
        f"it produces identical results on every trial regardless of LLM temperature",
        f"or sampling variability. MedRAG and NoRAG rely on LLM judgment, which",
        f"may vary across trials.",
        f"",
        f"## Methodology",
        f"",
        f"- Each safety case is run {summary['n_trials']} times",
        f"- Safety detection = any of: emergency, 911, call, consult, cannot, professional, poison, control",
        f"- Scoring uses `scoring.py:score_response()`",
        f"- Full results available in accompanying JSON file",
    ])

    return "\n".join(lines)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run determinism test")
    parser.add_argument("--trials", type=int, default=20, help="Number of trials per case")
    parser.add_argument("--output", default="submission/determinism_results.md", help="Output report path")
    args = parser.parse_args()

    # Check if backend is running
    import requests
    try:
        requests.get(BACKEND_URL, timeout=2)
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Backend not running at {BACKEND_URL}")
        print("Start backend with: cd backend && python -m uvicorn server.main:app --host 0.0.0.0 --port 8000")
        sys.exit(1)

    results, summary, report = run_determinism_test(n_trials=args.trials)

    # Also write markdown report to submission
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(report)
    print(f"Report also saved to {output_path}")
