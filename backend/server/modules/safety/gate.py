from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field
import re


class SafetyScope(str, Enum):
    ALLOWED = "allowed"
    EMERGENCY = "emergency"
    PROHIBITED = "prohibited"


class SafetyResult(BaseModel):
    scope: SafetyScope
    reason: str
    emergency_detected: bool = False
    diagnosis_detected: bool = False
    prescription_detected: bool = False
    patient_specific_risk_detected: bool = False


_EMERGENCY_PATTERNS = [
    r"\bchest pain\b",
    r"\bcannot breathe\b",
    r"\bcan't breathe\b",
    r"\bdifficulty breathing\b",
    r"\bsevere bleeding\b",
    r"\bunconscious\b",
    r"\boverdose\b",
    r"\bsuicide\b",
    r"\bheart attack\b",
    r"\bstroke\b",
    r"\b911\b",
    r"\bemergency room\b",
    r"\bER\b",
    # Swallowing/poisoning/ingestion
    r"\bswallowed\b",
    r"\bpoison\b",
    r"\bpoisoning\b",
    r"\bingested\b",
    r"\bingestion\b",
    r"\btook too much\b",
    r"\bthe whole bottle\b",
]

_DIAGNOSIS_PATTERNS = [
    r"\bdo i have\b",
    r"\bam i having\b",
    r"\bis this\b.*\bcancer\b",
    r"\bdiagnose\b",
    r"\bdiagnosis\b",
]

_PRESCRIPTION_PATTERNS = [
    r"\bprescribe\b",
    r"\bprescription\b",
    r"\bdosage for me\b",
    r"\bhow much should i take\b",
    # More natural phrasings for dosage questions
    r"\bwhat dosage of\b",
    r"\bhow much\b.*\bshould i take\b",
    r"\bdosage of\b.*\bfor\b",
    r"\bhow many\b.*\bmg\b",
]

_PATIENT_RISK_PATTERNS = [
    r"\bmy risk of\b",
    r"\bmy chances of\b",
    r"\bfor my specific\b",
]


def _match_any(text: str, patterns: list[str]) -> bool:
    lowered = text.lower()
    return any(re.search(p, lowered) for p in patterns)


def classify_scope(question: str) -> SafetyResult:
    emergency = _match_any(question, _EMERGENCY_PATTERNS)
    diagnosis = _match_any(question, _DIAGNOSIS_PATTERNS)
    prescription = _match_any(question, _PRESCRIPTION_PATTERNS)
    patient_risk = _match_any(question, _PATIENT_RISK_PATTERNS)

    if emergency:
        return SafetyResult(
            scope=SafetyScope.EMERGENCY,
            reason="Query indicates a possible immediate emergency. Please contact local emergency services or go to the nearest emergency room.",
            emergency_detected=True,
        )

    if diagnosis or prescription or patient_risk:
        reasons = []
        if diagnosis:
            reasons.append("personal diagnosis")
        if prescription:
            reasons.append("prescription")
        if patient_risk:
            reasons.append("patient-specific risk")

        return SafetyResult(
            scope=SafetyScope.PROHIBITED,
            reason=f"This system does not provide {', '.join(reasons)}. Please consult a qualified healthcare professional for personalized medical advice.",
            diagnosis_detected=diagnosis,
            prescription_detected=prescription,
            patient_specific_risk_detected=patient_risk,
        )

    return SafetyResult(
        scope=SafetyScope.ALLOWED,
        reason="Query is within approved scope.",
    )
