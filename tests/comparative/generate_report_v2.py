"""
HTML report generator for Comparative Study v2.
Uses new scoring system with normalized [0, 1] scores.
"""

import json
import glob
import os
from datetime import datetime

from tests.comparative.scoring_v2 import compute_calibration, compute_aggregate_metrics
from tests.comparative.test_dataset_v2 import ACCURACY_SUITE_IDS, SAFETY_SUITE_IDS


def load_results():
    """Load all comparison results."""
    results = []
    for file in sorted(glob.glob("tests/comparative/results/run*.json")):
        with open(file) as f:
            results.append(json.load(f))
    return results


def calculate_metrics(results):
    """Calculate aggregate metrics per system."""
    systems = ["uq_rag", "medrag_baseline", "no_rag"]
    
    metrics = {}
    for system in systems:
        all_scores = []
        accuracy_scores = []
        safety_scores = []
        calibration_scores = []
        hallucination_scores = []
        
        for run_results in results:
            for q_result in run_results:
                score_data = q_result["scores"].get(system, {})
                score = score_data.get("score", 0)
                dimension = score_data.get("dimension", "")
                q_id = q_result["test_case"]["id"]
                
                all_scores.append(score)
                
                if dimension == "accuracy":
                    accuracy_scores.append(score)
                elif dimension == "safety":
                    safety_scores.append(score)
                elif dimension == "calibration":
                    calibration_scores.append(score)
                elif dimension == "hallucination":
                    hallucination_scores.append(score)
        
        metrics[system] = {
            "overall": compute_aggregate_metrics(all_scores),
            "accuracy": compute_aggregate_metrics(accuracy_scores),
            "safety": compute_aggregate_metrics(safety_scores),
            "calibration": compute_aggregate_metrics(calibration_scores),
            "hallucination": compute_aggregate_metrics(hallucination_scores),
        }
    
    return metrics


def generate_html_report():
    """Generate HTML comparison report for v2."""
    results = load_results()
    if not results:
        print("No results found. Run tests first.")
        return None
    
    metrics = calculate_metrics(results)
    winner = max(metrics.keys(), key=lambda s: metrics[s]["overall"]["mean"])
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>UQ-RAG Comparative Study Report v2</title>
<style>
body {{ font-family: 'Inter', Arial, sans-serif; padding: 40px; background: white; max-width: 1200px; margin: 0 auto; }}
h1 {{ color: #1565c0; }}
h2 {{ color: #4db6ac; border-bottom: 2px solid #4db6ac; padding-bottom: 8px; }}
table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
th {{ background: #1565c0; color: white; }}
tr:nth-child(even) {{ background: #f5f5f5; }}
.metric-good {{ color: #2e7d32; font-weight: bold; }}
.metric-bad {{ color: #c62828; font-weight: bold; }}
.comparison-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 20px 0; }}
.metric-card {{ background: #f5f5f5; padding: 20px; border-radius: 10px; text-align: center; }}
.metric-value {{ font-size: 32px; font-weight: bold; color: #1565c0; }}
.metric-label {{ font-size: 12px; color: #666; margin-top: 8px; }}
.winner {{ background: #e8f5e9; border: 2px solid #2e7d32; }}
</style>
</head>
<body>

<h1>UQ-RAG Comparative Study Report v2</h1>
<p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
<p>Runs: {len(results)} | Questions: 20 | Systems: 3</p>
<p>Winner: <strong class="metric-good">{winner}</strong> (Score: {metrics[winner]["overall"]["mean"]:.3f})</p>

<h2>Methodology</h2>
<p><strong>Scoring System:</strong> All scores normalized to [0, 1] interval.</p>
<ul>
<li><strong>Safety:</strong> Binary gating (1.0 = detected, 0.0 = missed)</li>
<li><strong>Accuracy:</strong> Keyword coverage + citation bonus (0.2 if sources present)</li>
<li><strong>Calibration:</strong> Doubt expression for unknown questions</li>
<li><strong>Hallucination:</strong> Correct abstention for unanswerable questions</li>
</ul>
<p><strong>Composite:</strong> Mean across all questions and runs. Statistical significance via 95% CI.</p>

<h2>Overall Performance</h2>
<div class="comparison-grid">
<div class="metric-card{' winner' if winner == 'uq_rag' else ''}">
<div class="metric-value{' metric-good' if winner == 'uq_rag' else ''}">{metrics['uq_rag']["overall"]["mean"]:.3f}</div>
<div class="metric-label">UQ-RAG<br>Mean Score</div>
</div>
<div class="metric-card{' winner' if winner == 'medrag_baseline' else ''}">
<div class="metric-value{' metric-good' if winner == 'medrag_baseline' else ''}">{metrics['medrag_baseline']["overall"]["mean"]:.3f}</div>
<div class="metric-label">MedRAG Baseline<br>Mean Score</div>
</div>
<div class="metric-card{' winner' if winner == 'no_rag' else ''}">
<div class="metric-value{' metric-good' if winner == 'no_rag' else ''}">{metrics['no_rag']["overall"]["mean"]:.3f}</div>
<div class="metric-label">No-RAG Baseline<br>Mean Score</div>
</div>
</div>

<h2>Detailed Metrics (Mean ± SD, 95% CI)</h2>
<table>
<tr>
<th>System</th>
<th>N</th>
<th>Mean</th>
<th>Std Dev</th>
<th>95% CI</th>
</tr>
"""

    for system in ["uq_rag", "medrag_baseline", "no_rag"]:
        m = metrics[system]["overall"]
        html += f"""<tr>
<td><strong>{system}</strong></td>
<td>{m['n']}</td>
<td>{m['mean']:.3f}</td>
<td>{m['std']:.3f}</td>
<td>[{m['ci_95'][0]:.3f}, {m['ci_95'][1]:.3f}]</td>
</tr>"""

    html += """
</table>

<h2>Dimension Breakdown</h2>
<table>
<tr>
<th>System</th>
<th>Accuracy</th>
<th>Safety</th>
<th>Calibration</th>
<th>Hallucination</th>
</tr>
"""

    for system in ["uq_rag", "medrag_baseline", "no_rag"]:
        html += f"<tr><td><strong>{system}</strong></td>"
        for dim in ["accuracy", "safety", "calibration", "hallucination"]:
            m = metrics[system].get(dim, {})
            if m:
                html += f"<td>{m['mean']:.3f} ± {m['std']:.3f}</td>"
            else:
                html += "<td>N/A</td>"
        html += "</tr>"

    html += """
</table>

<h2>Per-Question Results (Latest Run)</h2>
<table>
<tr>
<th>ID</th>
<th>Question</th>
<th>Category</th>
<th>UQ-RAG</th>
<th>MedRAG</th>
<th>No-RAG</th>
</tr>
"""

    # Use latest run for per-question display
    latest_run = results[-1] if results else []
    for q_result in latest_run:
        tc = q_result["test_case"]
        q_id = tc["id"]
        question = tc.get("question", "?")[:60]
        category = tc.get("category", "?")
        
        uq = q_result["scores"].get("uq_rag", {}).get("score", "N/A")
        medrag = q_result["scores"].get("medrag_baseline", {}).get("score", "N/A")
        norag = q_result["scores"].get("no_rag", {}).get("score", "N/A")
        
        html += f"""<tr>
<td>{q_id}</td>
<td>{question}...</td>
<td>{category}</td>
<td>{uq}</td>
<td>{medrag}</td>
<td>{norag}</td>
</tr>"""

    html += """
</table>

<h2>Conclusions</h2>
<ul>
<li>Safety detection is properly rewarded as a gating criterion</li>
<li>Document-specific questions test retrieval value</li>
<li>Normalized scoring enables valid statistical comparison</li>
<li>Confidence intervals assess result reliability</li>
</ul>

<h2>Limitations</h2>
<ul>
<li>Small sample size (N=20) limits statistical power</li>
<li>Single document corpus (aspirin only)</li>
<li>No human evaluation of answer quality</li>
<li>Automated keyword matching has false negatives</li>
</ul>

</body>
</html>"""

    os.makedirs("docs", exist_ok=True)
    with open("docs/comparative_study_report_v2.html", "w") as f:
        f.write(html)

    print(f"Report generated: docs/comparative_study_report_v2.html")
    print(f"Winner: {winner} (score: {metrics[winner]['overall']['mean']:.3f})")
    
    return metrics


if __name__ == "__main__":
    generate_html_report()
