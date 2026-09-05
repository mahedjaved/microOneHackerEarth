"""Tests for risk_coverage.py."""

import json
import math
import os
import tempfile
from pathlib import Path

import numpy as np
import pytest

# Ensure backend directory is on path for script imports
backend_dir = Path(__file__).parent.parent.parent
import sys
sys.path.insert(0, str(backend_dir))

from scripts.risk_coverage import (
    load_claims,
    risk_coverage_curve,
    compute_auc,
    bootstrap_auc_ci,
    generate_risk_coverage_artifact,
    compare_clean_adversarial,
    ablate,
    cohens_d,
)


class TestLoadClaims:
    def test_load_valid_jsonl(self, tmp_path):
        claims = [
            {"claim_id": "c1", "support_probability": 0.9, "is_correct": True},
            {"claim_id": "c2", "support_probability": 0.3, "is_correct": False},
        ]
        p = tmp_path / "claims.jsonl"
        with open(p, "w") as f:
            for c in claims:
                f.write(json.dumps(c) + "\n")
        result = load_claims(str(p))
        assert len(result) == 2
        assert result[0]["claim_id"] == "c1"

    def test_load_skips_blank_lines(self, tmp_path):
        p = tmp_path / "claims.jsonl"
        with open(p, "w") as f:
            f.write("\n")
            f.write(json.dumps({"claim_id": "c1"}) + "\n")
            f.write("\n")
        result = load_claims(str(p))
        assert len(result) == 1

    def test_load_malformed_json_raises(self, tmp_path):
        p = tmp_path / "claims.jsonl"
        with open(p, "w") as f:
            f.write("not json\n")
        with pytest.raises(ValueError, match="Malformed JSON"):
            load_claims(str(p))


class TestRiskCoverageCurve:
    def test_basic_curve(self):
        claims = [
            {"support_probability": 0.9, "is_correct": True},
            {"support_probability": 0.8, "is_correct": True},
            {"support_probability": 0.3, "is_correct": False},
            {"support_probability": 0.2, "is_correct": False},
        ]
        thresholds, coverage, risk = risk_coverage_curve(claims, thresholds=[0.0, 0.5, 1.0])
        assert len(thresholds) == 3
        assert coverage[0] == 1.0  # all answered at threshold 0.0
        assert coverage[2] == 0.0  # none answered at threshold 1.0
        # At threshold 0.5, claims with prob >= 0.5 are answered: 2 out of 4
        assert coverage[1] == 0.5
        # Risk among answered at 0.5: both are correct, so risk = 0.0
        assert risk[1] == 0.0

    def test_no_answered_claims_returns_none_risk(self):
        claims = [
            {"support_probability": 0.1, "is_correct": True},
            {"support_probability": 0.2, "is_correct": False},
        ]
        thresholds, coverage, risk = risk_coverage_curve(claims, thresholds=[0.9, 1.0])
        assert risk[0] is None
        assert risk[1] is None
        assert coverage[0] == 0.0
        assert coverage[1] == 0.0

    def test_default_thresholds(self):
        claims = [
            {"support_probability": 0.5, "is_correct": True},
        ]
        thresholds, coverage, risk = risk_coverage_curve(claims)
        assert len(thresholds) == 51
        assert thresholds[0] == 0.0
        assert thresholds[-1] == 1.0


class TestComputeAuc:
    def test_perfect_classifier(self):
        thresholds = [0.0, 0.5, 1.0]
        risk = [0.5, 0.0, 0.0]  # risk decreases as coverage decreases
        auc = compute_auc(thresholds, risk)
        assert auc == 0.125  # trapezoidal integration

    def test_worst_classifier(self):
        thresholds = [0.0, 0.5, 1.0]
        risk = [0.5, 0.5, 1.0]  # risk stays high
        auc = compute_auc(thresholds, risk)
        assert auc == 0.625

    def test_none_risk_treated_as_one(self):
        thresholds = [0.0, 0.5, 1.0]
        risk = [0.5, None, 1.0]
        auc = compute_auc(thresholds, risk)
        # None -> 1.0, so risk sequence is [0.5, 1.0, 1.0]
        assert auc == 0.875


class TestBootstrapAucCi:
    def test_bootstrap_returns_three_values(self):
        claims = [
            {"support_probability": 0.9, "is_correct": True},
            {"support_probability": 0.8, "is_correct": True},
            {"support_probability": 0.3, "is_correct": False},
            {"support_probability": 0.2, "is_correct": False},
        ]
        auc, ci_low, ci_high = bootstrap_auc_ci(claims, n_bootstrap=100, random_state=42)
        assert 0.0 <= auc <= 1.0
        assert ci_low <= auc <= ci_high

    def test_bootstrap_reproducible_with_seed(self):
        claims = [
            {"support_probability": 0.9, "is_correct": True},
            {"support_probability": 0.8, "is_correct": True},
        ]
        auc1, low1, high1 = bootstrap_auc_ci(claims, n_bootstrap=50, random_state=42)
        auc2, low2, high2 = bootstrap_auc_ci(claims, n_bootstrap=50, random_state=42)
        assert auc1 == auc2
        assert low1 == low2
        assert high1 == high2


class TestGenerateRiskCoverageArtifact:
    def test_generates_json_and_png(self, tmp_path):
        claims = [
            {"claim_id": "c1", "support_probability": 0.9, "is_correct": True,
             "conformal_set": ["SUPPORTED"], "perturbation_type": "clean",
             "pipeline_mode": "full", "run_artifact_id": "run-1", "question_id": "q1"},
            {"claim_id": "c2", "support_probability": 0.3, "is_correct": False,
             "conformal_set": ["INSUFFICIENT"], "perturbation_type": "clean",
             "pipeline_mode": "full", "run_artifact_id": "run-1", "question_id": "q1"},
        ]
        output_json = str(tmp_path / "risk_coverage.json")
        artifact = generate_risk_coverage_artifact(claims, output_json, n_bootstrap=100)
        assert Path(output_json).exists()
        assert "auc" in artifact
        assert "thresholds" in artifact
        assert "coverage" in artifact
        assert "risk" in artifact
        assert artifact["n_claims"] == 2
        # PNG is optional depending on matplotlib availability
        png_path = Path(output_json).with_suffix(".png")
        if png_path.exists():
            assert png_path.stat().st_size > 0


class TestCompareCleanAdversarial:
    def test_compares_clean_vs_adversarial(self, tmp_path):
        claims = [
            {"claim_id": "c1", "support_probability": 0.9, "is_correct": True,
             "perturbation_type": "clean", "question_id": "q1"},
            {"claim_id": "c2", "support_probability": 0.3, "is_correct": False,
             "perturbation_type": "adversarial", "question_id": "q1"},
        ]
        output_path = str(tmp_path / "comparison.json")
        result = compare_clean_adversarial(claims, output_path)
        assert result["clean"]["n"] == 1
        assert result["adversarial"]["n"] == 1
        assert result["clean"]["avg_support_probability"] == 0.9
        assert result["adversarial"]["avg_support_probability"] == 0.3
        assert Path(output_path).exists()


class TestAblate:
    def test_ablate_compares_configs(self, tmp_path):
        claims_a = [
            {"claim_id": "c1", "support_probability": 0.9, "is_correct": True,
             "conformal_set": ["SUPPORTED"], "question_id": "q1", "pipeline_mode": "full"},
        ]
        claims_b = [
            {"claim_id": "c1", "support_probability": 0.8, "is_correct": True,
             "conformal_set": ["SUPPORTED"], "question_id": "q1", "pipeline_mode": "abstention_suppressed"},
        ]
        output_path = str(tmp_path / "ablation.json")
        result = ablate(claims_a, claims_b, output_path)
        assert result["config_a"] == "full"
        assert result["config_b"] == "abstention_suppressed"
        assert result["n_questions"] == 1
        assert "accuracy_delta" in result
        assert "abstention_rate_delta" in result
        assert "safety_detection_delta" in result
        assert "effect_size" in result
        assert Path(output_path).exists()

    def test_ablate_no_common_questions_raises(self):
        claims_a = [{"question_id": "q1", "support_probability": 0.9, "is_correct": True, "conformal_set": ["SUPPORTED"]}]
        claims_b = [{"question_id": "q2", "support_probability": 0.8, "is_correct": True, "conformal_set": ["SUPPORTED"]}]
        with pytest.raises(ValueError, match="No common questions"):
            ablate(claims_a, claims_b, "tmp.json")


class TestCohensD:
    def test_no_effect(self):
        assert cohens_d([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == 0.0

    def test_positive_effect(self):
        d = cohens_d([5.0, 6.0, 7.0], [1.0, 2.0, 3.0])
        assert d > 0

    def test_single_value_returns_zero(self):
        assert cohens_d([1.0], [2.0]) == 0.0
