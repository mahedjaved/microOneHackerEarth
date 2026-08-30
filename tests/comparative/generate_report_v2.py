"""
Generate HTML report with charts for UQ-RAG comparative study.

Creates a comprehensive dashboard showing:
1. Risk-coverage curve
2. ECE/reliability diagram
3. ROC curve for retrieval threshold
4. Per-system metrics comparison
5. Per-question detailed results
"""

import json
import os
from pathlib import Path
from datetime import datetime


def load_json(path: str) -> dict:
    """Load JSON file."""
    with open(path) as f:
        return json.load(f)


def generate_html_report(analysis_dir: str, results_dir: str, output_path: str):
    """Generate comprehensive HTML report with embedded charts."""

    # Load analysis data
    risk_coverage = load_json(os.path.join(analysis_dir, "risk_coverage.json"))
    ece_data = load_json(os.path.join(analysis_dir, "ece_reliability.json"))
    roc_data = load_json(os.path.join(analysis_dir, "roc_retrieval.json"))
    metrics = load_json(os.path.join(analysis_dir, "system_metrics.json"))

    # Generate Chart.js data
    risk_coverage_chart = {
        "type": "line",
        "data": {
            "labels": [f"{p['alpha']:.2f}" for p in risk_coverage["curve"]],
            "datasets": [
                {
                    "label": "Coverage",
                    "data": [p["coverage"] for p in risk_coverage["curve"]],
                    "borderColor": "rgb(75, 192, 192)",
                    "tension": 0.1
                },
                {
                    "label": "Risk (1 - Coverage)",
                    "data": [p["risk"] for p in risk_coverage["curve"]],
                    "borderColor": "rgb(255, 99, 132)",
                    "tension": 0.1
                }
            ]
        },
        "options": {
            "responsive": True,
            "plugins": {
                "title": {"display": True, "text": f"Risk-Coverage Curve (quantile={risk_coverage['quantile']})"}
            },
            "scales": {
                "x": {"title": {"display": True, "text": "Alpha (significance level)"}},
                "y": {"title": {"display": True, "text": "Rate"}, "min": 0, "max": 1}
            }
        }
    }

    ece_chart = {
        "type": "bar",
        "data": {
            "labels": [b["bin"] for b in ece_data["bins"] if b["count"] > 0],
            "datasets": [
                {
                    "label": "Accuracy",
                    "data": [b["accuracy"] for b in ece_data["bins"] if b["count"] > 0],
                    "backgroundColor": "rgba(75, 192, 192, 0.5)"
                },
                {
                    "label": "Confidence",
                    "data": [b["confidence"] for b in ece_data["bins"] if b["count"] > 0],
                    "backgroundColor": "rgba(255, 99, 132, 0.5)"
                }
            ]
        },
        "options": {
            "responsive": True,
            "plugins": {
                "title": {"display": True, "text": f"Reliability Diagram (ECE={ece_data['ece']:.3f})"}
            },
            "scales": {
                "x": {"title": {"display": True, "text": "Confidence Bin"}},
                "y": {"title": {"display": True, "text": "Rate"}, "min": 0, "max": 1}
            }
        }
    }

    roc_chart = {
        "type": "line",
        "data": {
            "labels": [f"{p['fpr']:.2f}" for p in roc_data["curve"][::5]],
            "datasets": [
                {
                    "label": f"ROC (AUC={roc_data['auc']:.3f})",
                    "data": [p["tpr"] for p in roc_data["curve"][::5]],
                    "borderColor": "rgb(75, 192, 192)",
                    "tension": 0.1,
                    "fill": False
                },
                {
                    "label": "Random",
                    "data": [p["fpr"] for p in roc_data["curve"][::5]],
                    "borderColor": "rgb(200, 200, 200)",
                    "borderDash": [5, 5],
                    "tension": 0.1,
                    "fill": False
                }
            ]
        },
        "options": {
            "responsive": True,
            "plugins": {
                "title": {"display": True, "text": "ROC Curve for Retrieval Threshold"}
            },
            "scales": {
                "x": {"title": {"display": True, "text": "False Positive Rate"}},
                "y": {"title": {"display": True, "text": "True Positive Rate"}}
            }
        }
    }

    # System comparison chart
    systems = list(metrics.keys())
    metric_names = ["safety_detection_rate", "doubt_expression_rate", "citation_rate", "hallucination_avoidance_rate"]
    metric_labels = ["Safety Detection", "Doubt Expression", "Citation Rate", "Hallucination Avoidance"]
    colors = [
        "rgba(75, 192, 192, 0.7)",
        "rgba(255, 99, 132, 0.7)",
        "rgba(54, 162, 235, 0.7)",
        "rgba(255, 206, 86, 0.7)"
    ]

    system_comparison_chart = {
        "type": "radar",
        "data": {
            "labels": metric_labels,
            "datasets": [
                {
                    "label": sys,
                    "data": [metrics[sys].get(m, 0) for m in metric_names],
                    "backgroundColor": colors[i % len(colors)],
                    "borderColor": colors[i % len(colors)].replace("0.7", "1")
                }
                for i, sys in enumerate(systems)
            ]
        },
        "options": {
            "responsive": True,
            "plugins": {
                "title": {"display": True, "text": "System Comparison by Metric"}
            },
            "scales": {
                "r": {"min": 0, "max": 1}
            }
        }
    }

    # Score comparison bar chart
    score_comparison_chart = {
        "type": "bar",
        "data": {
            "labels": [s.replace("_", " ").title() for s in systems],
            "datasets": [
                {
                    "label": "Mean Score",
                    "data": [metrics[s].get("mean_score", 0) for s in systems],
                    "backgroundColor": colors[:len(systems)]
                },
                {
                    "label": "Error Rate",
                    "data": [metrics[s].get("error_rate", 0) for s in systems],
                    "backgroundColor": "rgba(200, 200, 200, 0.5)"
                }
            ]
        },
        "options": {
            "responsive": True,
            "plugins": {
                "title": {"display": True, "text": "Mean Score and Error Rate by System"}
            },
            "scales": {
                "y": {"min": 0, "max": 1}
            }
        }
    }

    # Dimension breakdown chart
    dimensions = ["accuracy", "safety", "calibration", "hallucination"]
    dimension_chart = {
        "type": "bar",
        "data": {
            "labels": [d.title() for d in dimensions],
            "datasets": [
                {
                    "label": sys.replace("_", " ").title(),
                    "data": [metrics[sys].get("dimension_avgs", {}).get(d, 0) for d in dimensions],
                    "backgroundColor": colors[i % len(colors)]
                }
                for i, sys in enumerate(systems)
            ]
        },
        "options": {
            "responsive": True,
            "plugins": {
                "title": {"display": True, "text": "Score by Dimension"}
            },
            "scales": {
                "y": {"min": 0, "max": 1}
            }
        }
    }

    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UQ-RAG Comparative Study - Analysis Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        h1 {{
            color: #333;
            text-align: center;
            margin-bottom: 10px;
        }}
        .subtitle {{
            text-align: center;
            color: #666;
            margin-bottom: 30px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .chart-container {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .chart-title {{
            font-size: 14px;
            font-weight: 600;
            color: #555;
            margin-bottom: 10px;
        }}
        .metrics-table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metrics-table th, .metrics-table td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        .metrics-table th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #333;
        }}
        .metrics-table tr:hover {{
            background: #f8f9fa;
        }}
        .metric-good {{
            color: #28a745;
            font-weight: 600;
        }}
        .metric-warn {{
            color: #ffc107;
            font-weight: 600;
        }}
        .metric-bad {{
            color: #dc3545;
            font-weight: 600;
        }}
        .section-title {{
            font-size: 20px;
            font-weight: 600;
            color: #333;
            margin: 30px 0 15px 0;
            padding-bottom: 10px;
            border-bottom: 2px solid #eee;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>UQ-RAG Comparative Study Analysis</h1>
        <p class="subtitle">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <div class="section-title">Calibration Analysis</div>
        <div class="grid">
            <div class="chart-container">
                <canvas id="riskCoverageChart"></canvas>
            </div>
            <div class="chart-container">
                <canvas id="eceChart"></canvas>
            </div>
            <div class="chart-container">
                <canvas id="rocChart"></canvas>
            </div>
        </div>

        <div class="section-title">System Performance</div>
        <div class="grid">
            <div class="chart-container">
                <canvas id="systemComparisonChart"></canvas>
            </div>
            <div class="chart-container">
                <canvas id="scoreComparisonChart"></canvas>
            </div>
            <div class="chart-container">
                <canvas id="dimensionChart"></canvas>
            </div>
        </div>

        <div class="section-title">Summary Metrics</div>
        <table class="metrics-table">
            <thead>
                <tr>
                    <th>System</th>
                    <th>Mean Score</th>
                    <th>Std Dev</th>
                    <th>Error Rate</th>
                    <th>Safety Detection</th>
                    <th>Doubt Expression</th>
                    <th>Citation Rate</th>
                    <th>Hallucination Avoidance</th>
                </tr>
            </thead>
            <tbody>
                {"".join(f'''
                <tr>
                    <td><strong>{sys.replace("_", " ").title()}</strong></td>
                    <td>{metrics[sys].get("mean_score", 0):.3f}</td>
                    <td>{metrics[sys].get("std_score", 0):.3f}</td>
                    <td class="{'metric-bad' if metrics[sys].get('error_rate', 0) > 0.1 else 'metric-good'}">{metrics[sys].get('error_rate', 0):.1%}</td>
                    <td>{metrics[sys].get('safety_detection_rate', 0):.1%}</td>
                    <td>{metrics[sys].get('doubt_expression_rate', 0):.1%}</td>
                    <td>{metrics[sys].get('citation_rate', 0):.1%}</td>
                    <td>{metrics[sys].get('hallucination_avoidance_rate', 0):.1%}</td>
                </tr>
                ''' for sys in systems)}
            </tbody>
        </table>

        <div class="section-title">Key Findings</div>
        <div class="chart-container">
            <h3>Risk-Coverage Tradeoff</h3>
            <p>The saved conformal quantile ({risk_coverage['quantile']}) produces conservative predictions.
            At alpha=0.10, coverage is {next((p['coverage'] for p in risk_coverage['curve'] if abs(p['alpha'] - 0.10) < 0.01), 0):.1%},
            meaning the system abstains on questions it could answer correctly. Consider loosening alpha or
            enriching the calibration set with adversarial cases.</p>

            <h3>Verifier Calibration (ECE={ece_data['ece']:.3f})</h3>
            <p>Expected Calibration Error measures how well confidence matches accuracy.
            Lower is better. An ECE &lt; 0.05 indicates good calibration.</p>

            <h3>Retrieval Discrimination (AUC={roc_data['auc']:.3f})</h3>
            <p>Higher AUC means better separation between relevant and irrelevant documents.
            Use the ROC curve to select an optimal similarity threshold instead of fixed top-k.</p>
        </div>
    </div>

    <script>
        // Risk-Coverage Chart
        new Chart(document.getElementById('riskCoverageChart'), {json.dumps(risk_coverage_chart)});

        // ECE Reliability Chart
        new Chart(document.getElementById('eceChart'), {json.dumps(ece_chart)});

        // ROC Chart
        new Chart(document.getElementById('rocChart'), {json.dumps(roc_chart)});

        // System Comparison Radar Chart
        new Chart(document.getElementById('systemComparisonChart'), {json.dumps(system_comparison_chart)});

        // Score Comparison Chart
        new Chart(document.getElementById('scoreComparisonChart'), {json.dumps(score_comparison_chart)});

        // Dimension Breakdown Chart
        new Chart(document.getElementById('dimensionChart'), {json.dumps(dimension_chart)});
    </script>
</body>
</html>
"""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(html)

    print(f"Report generated: {output_path}")


if __name__ == "__main__":
    generate_html_report(
        analysis_dir="tests/comparative/analysis",
        results_dir="tests/comparative/results",
        output_path="tests/comparative/report.html"
    )
