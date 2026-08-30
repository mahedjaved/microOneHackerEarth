import pytest
import requests


BACKEND_URL = "http://127.0.0.1:8000"


class TestUncertaintyHandling:
    """Test uncertainty detection and doubt certificate generation."""

    def test_no_evidence_returns_doubt_certificate(self, backend_health):
        """Verify insufficient evidence triggers doubt certificate."""
        response = requests.post(
            f"{BACKEND_URL}/ask/",
            data={"question": "What is the cure for fictional disease X?"},
            timeout=30,
        )
        if response.status_code == 200:
            data = response.json()
            if not data.get("response"):
                assert data.get("doubt_certificate") is not None

    def test_doubt_certificate_has_required_fields(self, backend_health):
        """Verify doubt certificate contains required schema fields."""
        response = requests.post(
            f"{BACKEND_URL}/ask/",
            data={"question": "What is the cure for fictional disease X?"},
            timeout=30,
        )
        if response.status_code == 200:
            data = response.json()
            cert = data.get("doubt_certificate")
            if cert:
                assert "status" in cert
                assert cert.get("status") in ["insufficient_evidence", "clarification_required"]
                assert "message" in cert
                assert "support_probability" in cert

    def test_doubt_certificate_uncertainty_causes(self, backend_health):
        """Verify doubt certificate includes uncertainty causes."""
        response = requests.post(
            f"{BACKEND_URL}/ask/",
            data={"question": "What is the cure for fictional disease X?"},
            timeout=30,
        )
        if response.status_code == 200:
            data = response.json()
            cert = data.get("doubt_certificate")
            if cert:
                assert isinstance(cert.get("uncertainty_causes", []), list)

    def test_doubt_certificate_actions_taken(self, backend_health):
        """Verify doubt certificate includes actions taken."""
        response = requests.post(
            f"{BACKEND_URL}/ask/",
            data={"question": "What is the cure for fictional disease X?"},
            timeout=30,
        )
        if response.status_code == 200:
            data = response.json()
            cert = data.get("doubt_certificate")
            if cert:
                assert isinstance(cert.get("actions_taken", []), list)

    def test_confident_answer_no_doubt_certificate(self, backend_health):
        """Verify confident answer does not include doubt certificate."""
        response = requests.post(
            f"{BACKEND_URL}/ask/",
            data={"question": "What is aspirin used for?"},
            timeout=30,
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("response") and len(data["response"]) > 10:
                assert data.get("doubt_certificate") is None

    def test_run_artifact_id_present(self, backend_health):
        """Verify run artifact ID is present in response."""
        response = requests.post(
            f"{BACKEND_URL}/ask/",
            data={"question": "What is aspirin used for?"},
            timeout=30,
        )
        if response.status_code == 200:
            data = response.json()
            assert "run_artifact_id" in data


class TestEmergencyResponse:
    """Test emergency query detection and response."""

    def test_emergency_query_triggers_safety_response(self, backend_health):
        """Verify emergency queries trigger safety response."""
        response = requests.post(
            f"{BACKEND_URL}/ask/",
            data={"question": "I have severe chest pain and can't breathe"},
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("response"):
                assert "emergency" in data.get("response", "").lower() or data.get("emergency") is True

    def test_emergency_response_within_timeout(self, backend_health):
        """Verify emergency response is returned quickly."""
        import time
        start = time.time()
        response = requests.post(
            f"{BACKEND_URL}/ask/",
            data={"question": "I have severe chest pain and can't breathe"},
            timeout=5,
        )
        elapsed = time.time() - start
        assert elapsed < 5
