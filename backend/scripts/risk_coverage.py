#!/usr/bin/env python3
"""Risk-coverage curve generation and abstention analysis.

Usage:
    python scripts/risk_coverage.py --input data/runs/claims.jsonl --output data/runs/risk_coverage.json
    python scripts/risk_coverage.py --compare-clean-adversarial data/runs/claims.jsonl --output data/runs/perturbation_comparison.json
    python scripts/risk_coverage.py --ablate data/runs/claims_full.jsonl data/runs/claims_suppressed.jsonl --output data/runs/ablation.json
"""

import argparse
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_claims(path: str) -> list[dict]:
    """Load claim records from a JSONL file."""
    claims = []
    with open(path, "r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                claims.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"Malformed JSON at line {line_num}: {e}")
    return claims


# ---------------------------------------------------------------------------
# Risk-coverage curve
# ---------------------------------------------------------------------------

def risk_coverage_curve(
    claims: list[dict],
    thresholds: Optional[list[float]] = None,
) -> tuple[list[float], list[float], list[float]]:
    """Compute coverage and risk at each confidence threshold.

    Args:
        claims: List of claim records with `support_probability` and `is_correct`.
        thresholds: Confidence thresholds to sweep. Defaults to 0.0..1.0 in 0.02 steps.

    Returns:
        (thresholds, coverage, risk) — each list has the same length.
        `risk[i]` is `null` when no claims are answered at `thresholds[i]`.
    """
    if thresholds is None:
        thresholds = [round(i * 0.02, 2) for i in range(51)]

    probs = np.array([c["support_probability"] for c in claims])
    correct = np.array([c["is_correct"] for c in claims])

    coverage = []
    risk = []
    for t in thresholds:
        answered = probs >= t
        n_answered = int(answered.sum())
        if n_answered == 0:
            coverage.append(0.0)
            risk.append(None)
        else:
            coverage.append(n_answered / len(claims))
            risk.append(1.0 - float(correct[answered].mean()))

    return thresholds, coverage, risk


def compute_auc(thresholds: list[float], risk: list[float]) -> float:
    """Compute area under the risk-coverage curve via trapezoidal integration.

    Risk is treated as 1.0 for thresholds where risk is None (no claims answered).
    """
    # Replace None with 1.0 for integration (worst-case risk when nothing is answered)
    risk_filled = [1.0 if r is None else r for r in risk]
    auc = 0.0
    for i in range(1, len(thresholds)):
        x0, x1 = thresholds[i - 1], thresholds[i]
        y0, y1 = risk_filled[i - 1], risk_filled[i]
        auc += (x1 - x0) * (y0 + y1) / 2.0
    return float(auc)


def bootstrap_auc_ci(
    claims: list[dict],
    n_bootstrap: int = 1000,
    alpha: float = 0.05,
    random_state: Optional[int] = 42,
) -> tuple[float, float, float]:
    """Compute bootstrap confidence interval for AUC."""
    rng = np.random.RandomState(random_state)
    n = len(claims)
    aucs = []
    for _ in range(n_bootstrap):
        idx = rng.randint(0, n, size=n)
        sample = [claims[i] for i in idx]
        thresholds, coverage, risk = risk_coverage_curve(sample)
        aucs.append(compute_auc(thresholds, risk))
    aucs = np.array(aucs)
    auc = float(np.mean(aucs))
    ci_low = float(np.percentile(aucs, 100 * alpha / 2))
    ci_high = float(np.percentile(aucs, 100 * (1 - alpha / 2)))
    return auc, ci_low, ci_high


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_curve(
    thresholds: list[float],
    coverage: list[float],
    risk: list[float],
    auc: float,
    output_path: str,
) -> None:
    """Save a risk-coverage curve PNG."""
    try:
        import matplotlib.pyplot as plt
    except Exception as e:
        raise RuntimeError(f"matplotlib is required for plotting. Install with: pip install matplotlib ({e})")

    risk_filled = [1.0 if r is None else r for r in risk]

    fig, ax1 = plt.subplots(figsize=(8, 5))

    color = "tab:blue"
    ax1.set_xlabel("Confidence threshold")
    ax1.set_ylabel("Coverage", color=color)
    ax1.plot(thresholds, coverage, color=color, linewidth=2, label="Coverage")
    ax1.tick_params(axis="y", labelcolor=color)
    ax1.set_ylim(0, 1.05)

    ax2 = ax1.twinx()
    color = "tab:red"
    ax2.set_ylabel("Risk (error rate)", color=color)
    ax2.plot(thresholds, risk_filled, color=color, linewidth=2, linestyle="--", label="Risk")
    ax2.tick_params(axis="y", labelcolor=color)
    ax2.set_ylim(0, 1.05)

    fig.suptitle(f"Risk-Coverage Curve (AUC = {auc:.2f})")
    fig.tight_layout()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Calibration metadata
# ---------------------------------------------------------------------------

def load_calibration_metadata() -> dict:
    """Load calibration metadata from data/models/ if available."""
    meta_path = Path("data/models/calibration_metadata.json")
    if not meta_path.exists():
        return {}
    try:
        with open(meta_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def extract_calibration_metrics(claims: list[dict]) -> dict:
    """Extract calibration metadata from claims or fallback to model metadata."""
    # Try to compute Brier score and ECE from claims if enough data
    if len(claims) < 10:
        return {
            "calibration_brier": None,
            "calibration_ece": None,
            "calibration_warning": "calibration set too small for reliable Brier score",
        }

    probs = np.array([c["support_probability"] for c in claims])
    correct = np.array([c["is_correct"] for c in claims])

    # Brier score
    brier = float(np.mean((probs - correct) ** 2))

    # ECE (10-bin)
    n_bins = 10
    bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        mask = (probs > bin_boundaries[i]) & (probs <= bin_boundaries[i + 1])
        if mask.sum() > 0:
            bin_accuracy = correct[mask].mean()
            bin_confidence = probs[mask].mean()
            ece += mask.sum() * abs(bin_accuracy - bin_confidence)
    ece /= len(probs)

    return {
        "calibration_brier": round(brier, 4),
        "calibration_ece": round(ece, 4),
        "calibration_warning": None,
    }


# ---------------------------------------------------------------------------
# Artifact generation
# ---------------------------------------------------------------------------

def generate_risk_coverage_artifact(
    claims: list[dict],
    output_path: str,
    n_bootstrap: int = 1000,
) -> dict:
    """Generate and save a risk-coverage artifact."""
    thresholds, coverage, risk = risk_coverage_curve(claims)
    auc, ci_low, ci_high = bootstrap_auc_ci(claims, n_bootstrap=n_bootstrap)
    calibration = extract_calibration_metrics(claims)

    artifact = {
        "thresholds": thresholds,
        "coverage": coverage,
        "risk": risk,
        "auc": round(auc, 4),
        "auc_ci_low": round(ci_low, 4),
        "auc_ci_high": round(ci_high, 4),
        "n_claims": len(claims),
        "calibration_brier": calibration["calibration_brier"],
        "calibration_ece": calibration["calibration_ece"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "calibration_warning": calibration["calibration_warning"],
    }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(artifact, f, indent=2)

    # Also save PNG if matplotlib is available
    png_path = Path(output_path).with_suffix(".png")
    try:
        plot_curve(thresholds, coverage, risk, auc, str(png_path))
    except RuntimeError as e:
        print(f"WARNING: Could not generate plot: {e}")

    return artifact


# ---------------------------------------------------------------------------
# Adversarial comparison
# ---------------------------------------------------------------------------

def compare_clean_adversarial(claims: list[dict], output_path: str) -> dict:
    """Compare abstention behavior between clean and adversarial questions."""
    clean = [c for c in claims if c.get("perturbation_type") == "clean"]
    adversarial = [c for c in claims if c.get("perturbation_type") == "adversarial"]

    def summarize(subset: list[dict]) -> dict:
        if not subset:
            return {"n": 0, "abstention_rate": None, "avg_support_probability": None}
        probs = [c["support_probability"] for c in subset]
        abstentions = sum(1 for p in probs if p < 0.5)  # threshold 0.5 as proxy
        return {
            "n": len(subset),
            "abstention_rate": round(abstentions / len(subset), 4),
            "avg_support_probability": round(np.mean(probs), 4),
        }

    clean_summary = summarize(clean)
    adv_summary = summarize(adversarial)

    abstention_shift = None
    if clean_summary["abstention_rate"] is not None and adv_summary["abstention_rate"] is not None:
        abstention_shift = round(adv_summary["abstention_rate"] - clean_summary["abstention_rate"], 4)

    result = {
        "clean": clean_summary,
        "adversarial": adv_summary,
        "abstention_shift": abstention_shift,
        "larger_effect": None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    if abstention_shift is not None:
        result["larger_effect"] = "perturbation" if abs(abstention_shift) > 0.1 else "explicit_abstention_mechanism"

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    return result


# ---------------------------------------------------------------------------
# Ablation
# ---------------------------------------------------------------------------

def cohens_d(values_a: list[float], values_b: list[float]) -> float:
    """Compute Cohen's d effect size."""
    n1, n2 = len(values_a), len(values_b)
    if n1 < 2 or n2 < 2:
        return 0.0
    mean1, mean2 = np.mean(values_a), np.mean(values_b)
    var1, var2 = np.var(values_a, ddof=1), np.var(values_b, ddof=1)
    pooled_std = math.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
    return float((mean1 - mean2) / pooled_std)


def ablate(
    claims_a: list[dict],
    claims_b: list[dict],
    output_path: str,
    config_a: str = "full",
    config_b: str = "abstention_suppressed",
) -> dict:
    """Compare two pipeline configurations on the same question set."""
    # Group by question_id
    from collections import defaultdict

    def group_by_question(claims):
        grouped = defaultdict(list)
        for c in claims:
            grouped[c["question_id"]].append(c)
        return grouped

    group_a = group_by_question(claims_a)
    group_b = group_by_question(claims_b)

    common_questions = sorted(set(group_a.keys()) & set(group_b.keys()))
    if not common_questions:
        raise ValueError("No common questions found between the two claim sets.")

    accuracy_a, accuracy_b = [], []
    abstention_a, abstention_b = [], []
    safety_a, safety_b = [], []

    for qid in common_questions:
        ca = group_a[qid]
        cb = group_b[qid]

        # Accuracy: fraction of correct claims
        acc_a = np.mean([c["is_correct"] for c in ca]) if ca else 0.0
        acc_b = np.mean([c["is_correct"] for c in cb]) if cb else 0.0
        accuracy_a.append(acc_a)
        accuracy_b.append(acc_b)

        # Abstention rate: fraction of claims with support_probability < 0.5
        abst_a = np.mean([1 for c in ca if c["support_probability"] < 0.5]) if ca else 0.0
        abst_b = np.mean([1 for c in cb if c["support_probability"] < 0.5]) if cb else 0.0
        abstention_a.append(abst_a)
        abstention_b.append(abst_b)

        # Safety detection: fraction of claims with conformal set containing INSUFFICIENT
        safe_a = np.mean([1 for c in ca if "INSUFFICIENT" in c.get("conformal_set", [])]) if ca else 0.0
        safe_b = np.mean([1 for c in cb if "INSUFFICIENT" in c.get("conformal_set", [])]) if cb else 0.0
        safety_a.append(safe_a)
        safety_b.append(safe_b)

    accuracy_delta = float(np.mean(accuracy_a) - np.mean(accuracy_b))
    abstention_rate_delta = float(np.mean(abstention_a) - np.mean(abstention_b))
    safety_detection_delta = float(np.mean(safety_a) - np.mean(safety_b))
    effect_size = cohens_d(accuracy_a, accuracy_b)

    result = {
        "config_a": config_a,
        "config_b": config_b,
        "accuracy_delta": round(accuracy_delta, 4),
        "abstention_rate_delta": round(abstention_rate_delta, 4),
        "safety_detection_delta": round(safety_detection_delta, 4),
        "effect_size": round(effect_size, 4),
        "n_questions": len(common_questions),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Risk-coverage curve and abstention analysis")
    parser.add_argument("--input", help="Path to claims JSONL file")
    parser.add_argument("--output", required=True, help="Path to output JSON artifact")
    parser.add_argument("--compare-clean-adversarial", action="store_true", help="Compare clean vs adversarial abstention")
    parser.add_argument("--ablate", nargs=2, metavar=("FULL", "SUPPRESSED"), help="Ablate two claim JSONL files")
    parser.add_argument("--n-bootstrap", type=int, default=1000, help="Number of bootstrap samples for AUC CI")
    args = parser.parse_args()

    if args.compare_clean_adversarial:
        if not args.input:
            parser.error("--compare-clean-adversarial requires --input")
        claims = load_claims(args.input)
        result = compare_clean_adversarial(claims, args.output)
        print(json.dumps(result, indent=2))
    elif args.ablate:
        claims_a = load_claims(args.ablate[0])
        claims_b = load_claims(args.ablate[1])
        result = ablate(claims_a, claims_b, args.output)
        print(json.dumps(result, indent=2))
    elif args.input:
        claims = load_claims(args.input)
        if len(claims) < 30:
            print(f"WARNING: Only {len(claims)} claims loaded; conference-ready artifacts require >= 30.")
        artifact = generate_risk_coverage_artifact(claims, args.output, n_bootstrap=args.n_bootstrap)
        print(json.dumps(artifact, indent=2))
    else:
        parser.error("Must specify --input, --compare-clean-adversarial, or --ablate")


if __name__ == "__main__":
    main()
