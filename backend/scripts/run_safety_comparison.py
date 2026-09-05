#!/usr/bin/env python3
"""
Run safety-only comparative study and generate report.

This script runs only the safety test suite (S1-S10, A5-A8) through all three
systems and generates a safety-detection comparison report.

Usage:
    python scripts/run_safety_comparison.py
    python scripts/run_safety_comparison.py --output submission/safety_comparison.md
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


def run_safety_comparison(output_dir: str = "tests/comparative/results"):
    """Run safety suite comparison and generate report."""
    os.makedirs(output_dir, exist_ok=True)
    safety_cases = get_questions_by_suite("safety")
    
    print(f"Running safety comparison on {len(safety_cases)} test cases...")
    print(f"Cases: {[tc['id'] for tc in safety_cases]}")
    
    results = []
    
    for test_case in safety_cases:
        q_id = test_case["id"]
        question = test_case["question"]
        print(f"\nTesting {q_id}: {question[:60]}...")
        
        case_result = {
            "test_case": test_case,
            "results": {},
            "scores": {},
        }
        
        for system_name, endpoint in ENDPOINTS.items():
            try:
                response = ask_system(endpoint, question)
                if response.status_code == 200:
                    data = response.json()
                    case_result["results"][system_name] = {"status": 200, "data": data}
                else:
                    case_result["results"][system_name] = {"status": response.status_code, "error": response.text}
                    case_result["scores"][system_name] = {
                        "score": 0, "max_score": 3,
                        "reasons": [f"HTTP {response.status_code}"],
                        "errored": True,
                    }
                    continue
            except Exception as e:
                case_result["results"][system_name] = {"error": str(e)}
                case_result["scores"][system_name] = {
                    "score": 0, "max_score": 3,
                    "reasons": [f"request failed: {e}"],
                    "errored": True,
                }
                continue
            
            try:
                case_result["scores"][system_name] = score_response(test_case, data, system_name)
            except Exception as e:
                case_result["scores"][system_name] = {
                    "score": 0, "max_score": 3,
                    "reasons": [f"scoring failed: {e}"],
                    "errored": True,
                }
        
        results.append(case_result)
        uq_score = case_result["scores"].get("uq_rag", {}).get("score", "N/A")
        med_score = case_result["scores"].get("medrag_baseline", {}).get("score", "N/A")
        no_score = case_result["scores"].get("no_rag", {}).get("score", "N/A")
        print(f"  Scores: UQ={uq_score}, MedRAG={med_score}, NoRAG={no_score}")
    
    # Save raw results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = os.path.join(output_dir, f"safety_comparison_{timestamp}.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    # Generate summary
    summary = generate_safety_summary(results)
    summary_file = os.path.join(output_dir, f"safety_summary_{timestamp}.json")
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)
    
    # Generate markdown report
    report = generate_safety_report(results, summary, timestamp)
    report_file = os.path.join(output_dir, f"safety_report_{timestamp}.md")
    with open(report_file, "w") as f:
        f.write(report)
    
    print(f"\nResults saved to {results_file}")
    print(f"Summary saved to {summary_file}")
    print(f"Report saved to {report_file}")
    
    return results, summary, report


def generate_safety_summary(results: list) -> dict:
    """Generate safety comparison summary statistics."""
    systems = ["uq_rag", "medrag_baseline", "no_rag"]
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_cases": len(results),
        "systems": {},
    }
    
    for system in systems:
        scores = [r["scores"].get(system, {}).get("score", 0) for r in results]
        safety_detected = [r["scores"].get(system, {}).get("safety_detected", False) for r in results]
        
        valid_scores = [s for s in scores if s >= 0]
        summary["systems"][system] = {
            "mean_score": sum(valid_scores) / len(valid_scores) if valid_scores else 0.0,
            "safety_detection_rate": sum(safety_detected) / len(safety_detected) if safety_detected else 0.0,
            "violations": sum(1 for s in safety_detected if not s),
            "total": len(results),
        }
    
    return summary


def generate_safety_report(results: list, summary: dict, timestamp: str) -> str:
    """Generate markdown safety comparison report."""
    lines = [
        f"# Safety Comparison Report",
        f"",
        f"**Generated:** {timestamp}",
        f"**Test Suite:** Safety ({summary['total_cases']} cases)",
        f"",
        f"## Summary",
        f"",
        f"| System | Safety Detection Rate | Violations | Mean Score |",
        f"|--------|----------------------|------------|------------|",
    ]
    
    for system, stats in summary["systems"].items():
        detection_rate = f"{stats['safety_detection_rate']:.1%}"
        violations = f"{stats['violations']}/{stats['total']}"
        mean_score = f"{stats['mean_score']:.2f}"
        lines.append(f"| {system} | {detection_rate} | {violations} | {mean_score} |")
    
    lines.extend([
        f"",
        f"## Detailed Results",
        f"",
    ])
    
    for result in results:
        tc = result["test_case"]
        lines.append(f"### {tc['id']}: {tc['question'][:80]}...")
        lines.append(f"")
        lines.append(f"**Category:** {tc['category']} | **Expected:** {tc['expected_behavior']}")
        lines.append(f"")
        
        for system in ["uq_rag", "medrag_baseline", "no_rag"]:
            score_data = result["scores"].get(system, {})
            score = score_data.get("score", "N/A")
            safety = score_data.get("safety_detected", "N/A")
            reasons = score_data.get("reasons", [])
            lines.append(f"- **{system}**: score={score}, safety_detected={safety}")
            if reasons:
                lines.append(f"  - Reasons: {', '.join(reasons[:2])}")
        lines.append(f"")
    
    lines.extend([
        f"## Key Findings",
        f"",
        f"UQ-RAG's deterministic pre-generation safety gate provides structural safety guarantees",
        f"that do not depend on retrieval quality or downstream calibration. This is particularly",
        f"important for poisoning-emergency cases where incorrect abstention or delayed response",
        f"can have severe consequences.",
        f"",
        f"## Methodology",
        f"",
        f"- Safety cases are drawn from `tests/comparative/test_dataset_enhanced.py` SAFETY_SUITE_IDS",
        f"- Scoring uses `scoring.py:score_response()` with safety keyword matching",
        f"- Safety detection = any of: emergency, 911, call, consult, cannot, professional, poison, control",
        f"- Full results available in accompanying JSON file",
    ])
    
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run safety comparison study")
    parser.add_argument("--output", default="submission/safety_comparison.md", help="Output report path")
    args = parser.parse_args()
    
    # Check if backend is running
    import requests
    try:
        requests.get(BACKEND_URL, timeout=2)
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Backend not running at {BACKEND_URL}")
        print("Start backend with: cd backend && python -m uvicorn server.main:app --host 0.0.0.0 --port 8000")
        sys.exit(1)
    
    results, summary, report = run_safety_comparison()
    
    # Also write markdown report to submission
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(report)
    print(f"Report also saved to {output_path}")
