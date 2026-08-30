"""
Validation script for comparative study HTML report.
Verifies UQ-RAG advantages are displayed per T016.
"""

import os
import sys


def validate_report():
    """Validate that the HTML report shows UQ-RAG advantages."""
    report_path = "docs/comparative_study_report.html"

    if not os.path.exists(report_path):
        print("FAIL: Report not found at", report_path)
        return False

    with open(report_path, "r") as f:
        content = f.read()

    checks = []

    # Check report contains all three systems
    checks.append(("UQ-RAG mentioned", "UQ-RAG" in content))
    checks.append(("MedRAG mentioned", "MedRAG" in content or "medrag_baseline" in content))
    checks.append(("No-RAG mentioned", "No-RAG" in content or "no_rag" in content))

    # Check for required sections
    checks.append(("Executive Summary", "Executive Summary" in content))
    checks.append(("Per-Question Results", "Per-Question Results" in content))
    checks.append(("Accuracy Suite", "Accuracy-Prioritized" in content))
    checks.append(("Safety Suite", "Safety-Prioritized" in content))
    checks.append(("Composite Score", "Composite Score" in content))

    # Check for metrics
    checks.append(("Safety Rate", "Safety Detection Rate" in content))
    checks.append(("Doubt Rate", "Doubt Expression Rate" in content))
    checks.append(("Citation Rate", "Citation Rate" in content))
    checks.append(("Hallucination Rate", "Hallucination Rate" in content))

    # Check winner declaration
    checks.append(("Winner declared", "Winner:" in content or "winner" in content.lower()))

    all_passed = True
    for name, passed in checks:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_passed = False
        print(f"  [{status}] {name}")

    if all_passed:
        print("\nAll validation checks passed!")
    else:
        print("\nSome validation checks failed!")

    return all_passed


if __name__ == "__main__":
    success = validate_report()
    sys.exit(0 if success else 1)
