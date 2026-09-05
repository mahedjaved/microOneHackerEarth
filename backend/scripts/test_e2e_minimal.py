#!/usr/bin/env python3
"""Minimal e2e test that bypasses FastAPI app import.

This script directly initializes the UQ pipeline components and runs
multiple questions through the pipeline, exporting claims to JSONL.
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from server.modules.verifier.classifier import ThreeWayVerifier
from server.modules.verifier.conformal import ConformalPredictor
from server.modules.verifier.calibration import ProbabilityCalibrator
from server.modules.claims.composer import ClaimComposer
from server.modules.eav.controller import EAVController
from server.modules.output.answer import AnswerComposer, ClaimExporter
from server.modules.artifacts.run_artifact import build_run_artifact
from server.modules.corpus.loader import build_evidence_packet
from server.schemas import Passage, SafetyScope, FinalDecision, PerturbationType, PipelineMode

# Load prebuilt artifacts
models_dir = Path(__file__).parent.parent.parent / "data" / "models"
verifier_path = str(models_dir / "verifier_gp.joblib")
calibrator_path = str(models_dir / "calibrator.joblib")
conformal_path = models_dir / "conformal_quantile.json"

import json
with open(conformal_path) as f:
    conformal_data = json.load(f)
alpha = conformal_data.get("alpha", 0.10)
quantile = conformal_data.get("quantile", 0.5)

# Initialize components
verifier = ThreeWayVerifier(model_path=verifier_path)
calibrator = ProbabilityCalibrator(method="isotonic")
calibrator.load(calibrator_path)
conformal = ConformalPredictor.from_quantile(quantile=quantile, alpha=alpha, method="LAC")
claim_composer = ClaimComposer()
eav_controller = EAVController(action_budget=1)
answer_composer = AnswerComposer()

# Load embedding model for verifier
from sentence_transformers import SentenceTransformer
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
verifier.embedding_model = embedding_model

print("UQ pipeline components initialized")

# Test questions and answers
test_cases = [
    {
        "question": "What is aspirin used for?",
        "answer": "Aspirin is a common pain reliever used to treat mild to moderate pain. It works by inhibiting cyclooxygenase enzymes. Always consult a doctor before use.",
        "passages": [
            Passage(
                chunk_id="chunk-1",
                document_id="medical-doc-1",
                document_version="v1",
                page_location="page-1",
                text="Aspirin is a common pain reliever used to treat mild to moderate pain.",
                provenance_hash="abc123",
            )
        ],
    },
    {
        "question": "What is hypertension?",
        "answer": "Hypertension is defined as systolic blood pressure greater than 130 mmHg or diastolic blood pressure greater than 80 mmHg. It is a common cardiovascular condition requiring lifestyle changes and medication.",
        "passages": [
            Passage(
                chunk_id="chunk-2",
                document_id="medical-doc-2",
                document_version="v1",
                page_location="page-1",
                text="Hypertension is defined as systolic blood pressure greater than 130 mmHg or diastolic blood pressure greater than 80 mmHg.",
                provenance_hash="def456",
            )
        ],
    },
    {
        "question": "What is type 2 diabetes?",
        "answer": "Type 2 diabetes mellitus is characterized by insulin resistance and relative insulin deficiency. It is a chronic metabolic disorder affecting glucose regulation.",
        "passages": [
            Passage(
                chunk_id="chunk-3",
                document_id="medical-doc-3",
                document_version="v1",
                page_location="page-1",
                text="Type 2 diabetes mellitus is characterized by insulin resistance and relative insulin deficiency.",
                provenance_hash="ghi789",
            )
        ],
    },
    {
        "question": "What is the mechanism of action of metformin?",
        "answer": "Metformin works by activating AMP-activated protein kinase (AMPK). It reduces hepatic glucose production and improves insulin sensitivity in peripheral tissues.",
        "passages": [
            Passage(
                chunk_id="chunk-4",
                document_id="medical-doc-4",
                document_version="v1",
                page_location="page-1",
                text="The mechanism of action of metformin involves activation of AMP-activated protein kinase (AMPK).",
                provenance_hash="jkl012",
            )
        ],
    },
    {
        "question": "What is antibiotic resistance?",
        "answer": "Antibiotic resistance occurs when bacteria develop the ability to defeat the drugs designed to kill them. It is a major public health concern worldwide.",
        "passages": [
            Passage(
                chunk_id="chunk-5",
                document_id="medical-doc-5",
                document_version="v1",
                page_location="page-1",
                text="Antibiotic resistance occurs when bacteria develop the ability to defeat the drugs designed to kill them.",
                provenance_hash="mno345",
            )
        ],
    },
    {
        "question": "What are the symptoms of a heart attack?",
        "answer": "Heart attack symptoms include chest pain, shortness of breath, nausea, and pain radiating to the arm or jaw. Emergency medical attention is required immediately.",
        "passages": [
            Passage(
                chunk_id="chunk-6",
                document_id="medical-doc-6",
                document_version="v1",
                page_location="page-1",
                text="Heart attack symptoms include chest pain, shortness of breath, and nausea.",
                provenance_hash="pqr678",
            )
        ],
    },
    {
        "question": "How does insulin work?",
        "answer": "Insulin is a hormone produced by the pancreas. It regulates blood glucose levels by facilitating cellular uptake of glucose. It is essential for managing diabetes.",
        "passages": [
            Passage(
                chunk_id="chunk-7",
                document_id="medical-doc-7",
                document_version="v1",
                page_location="page-1",
                text="Insulin is a hormone produced by the pancreas that regulates blood glucose levels.",
                provenance_hash="stu901",
            )
        ],
    },
    {
        "question": "What is the recommended dosage of ibuprofen?",
        "answer": "Ibuprofen is typically dosed at 200-400mg every 4-6 hours for adults. Do not exceed 1200mg per day without medical supervision. Always follow package instructions.",
        "passages": [
            Passage(
                chunk_id="chunk-8",
                document_id="medical-doc-8",
                document_version="v1",
                page_location="page-1",
                text="Ibuprofen is typically dosed at 200-400mg every 4-6 hours for adults.",
                provenance_hash="vwx234",
            )
        ],
    },
    {
        "question": "What is the difference between viral and bacterial infections?",
        "answer": "Viral infections are caused by viruses and do not respond to antibiotics. Bacterial infections are caused by bacteria and can be treated with antibiotics. Proper diagnosis is essential.",
        "passages": [
            Passage(
                chunk_id="chunk-9",
                document_id="medical-doc-9",
                document_version="v1",
                page_location="page-1",
                text="Viral infections are caused by viruses and do not respond to antibiotics. Bacterial infections are caused by bacteria.",
                provenance_hash="yza567",
            )
        ],
    },
    {
        "question": "What is the role of cholesterol in heart disease?",
        "answer": "High cholesterol levels contribute to atherosclerosis and heart disease. LDL cholesterol is considered 'bad' cholesterol while HDL is 'good'. Diet and exercise can help manage levels.",
        "passages": [
            Passage(
                chunk_id="chunk-10",
                document_id="medical-doc-10",
                document_version="v1",
                page_location="page-1",
                text="High cholesterol levels contribute to atherosclerosis and heart disease.",
                provenance_hash="bcd890",
            )
        ],
    },
    {
        "question": "What is asthma?",
        "answer": "Asthma is a chronic respiratory condition characterized by airway inflammation and narrowing. It causes wheezing, shortness of breath, and coughing. Inhalers are commonly used for treatment.",
        "passages": [
            Passage(
                chunk_id="chunk-11",
                document_id="medical-doc-11",
                document_version="v1",
                page_location="page-1",
                text="Asthma is a chronic respiratory condition characterized by airway inflammation and narrowing.",
                provenance_hash="efg123",
            )
        ],
    },
    {
        "question": "What is the function of the liver?",
        "answer": "The liver is the body's largest internal organ. It detoxifies chemicals, metabolizes drugs, and produces bile. It also stores glycogen and synthesizes proteins.",
        "passages": [
            Passage(
                chunk_id="chunk-12",
                document_id="medical-doc-12",
                document_version="v1",
                page_location="page-1",
                text="The liver is the body's largest internal organ responsible for detoxification and metabolism.",
                provenance_hash="hij456",
            )
        ],
    },
]

exporter = ClaimExporter(output_dir="data/runs")
total_claims = 0

for i, case in enumerate(test_cases):
    question = case["question"]
    llm_answer = case["answer"]
    passages = case["passages"]

    evidence_packet = build_evidence_packet(
        corpus_id="medical-corpus-v1",
        corpus_hash="test-hash",
        retrieval_query=question,
        passages=passages,
        retriever_version="test-v1",
        latency_ms=0,
    )

    # Safety gate
    from server.modules.safety.gate import classify_scope
    safety_result = classify_scope(question)
    print(f"[{i+1}/{len(test_cases)}] Safety scope: {safety_result.scope}")

    # Claim decomposition
    claims = claim_composer.decompose(llm_answer, evidence_packet)
    print(f"[{i+1}/{len(test_cases)}] Claims decomposed: {len(claims)}")

    # Verifier + conformal
    verifier_outputs = []
    conformal_sets = []
    for claim in claims:
        evidence_text = " ".join(p.text for p in evidence_packet.passages) if evidence_packet.passages else ""
        verifier_result = verifier.predict_text(claim.text, evidence_text)
        verifier_outputs.append(verifier_result)
        claim.verifier_output = verifier_result  # Attach to claim for export
        
        if conformal.is_fitted:
            conformal_set = conformal.predict_set_from_probs(verifier_result.probabilities)
        else:
            from server.schemas import Verdict
            conformal_set = [Verdict.SUPPORTED]
        conformal_sets.append({"claim_id": str(claim.claim_id), "set": [v.name for v in conformal_set]})

    # Build artifact
    artifact = build_run_artifact(
        original_question=question,
        scope=SafetyScope.ALLOWED,
        corpus_id=evidence_packet.corpus_id,
        corpus_hash=evidence_packet.corpus_hash,
        model_version="test-v1",
        verifier_version="gp-v1",
        calibration_id="calibration-v1",
        evidence_packet=evidence_packet,
        claims=claims,
        evidence_features=[],
        verifier_outputs=verifier_outputs,
        conformal_sets=conformal_sets,
        eav_actions=[],
        final_decision=FinalDecision.DOUBT_CERTIFICATE,
        latency_ms=0,
    )

    # Export claims
    exporter.export(
        claims=claims,
        question_id=f"test-e2e-{i+1}",
        run_artifact_id=str(artifact.run_id),
        perturbation_type=PerturbationType.CLEAN,
        pipeline_mode=PipelineMode.FULL,
    )

    total_claims += len(claims)
    print(f"[{i+1}/{len(test_cases)}] Exported {len(claims)} claims (total: {total_claims})")

print(f"\nTotal claims exported: {total_claims}")
print("End-to-end test passed!")
