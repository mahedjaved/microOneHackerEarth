"""
Emergency safety response per Article IV.
"""

from server.schemas import FinalDecision


def build_safety_response() -> dict:
    """
    Return emergency safety response.

    Bypasses all retrieval and generation.
    """
    return {
        "final_decision": FinalDecision.SAFETY_RESPONSE,
        "response": None,
        "sources": [],
        "doubt_certificate": None,
        "disclaimer": "If you are experiencing a medical emergency, please call your local emergency services (such as 911) or go to the nearest emergency room immediately. This system is not for emergency medical care.",
        "injection_detected": False,
        "pii_redacted": False,
    }

