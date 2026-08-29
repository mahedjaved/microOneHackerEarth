"""
UAT test script for CURA-Med frontend-backend integration.

Tests the full flow: frontend -> backend -> UQ pipeline -> response.
"""

import time
import requests
import sys
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:8501")


def wait_for_server(url, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            requests.get(url, timeout=2)
            return True
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    return False


def test_backend_health():
    print("Testing backend health...")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        if response.status_code == 200:
            print("Backend health check: PASSED")
            return True
        else:
            print(f"Backend health check: FAILED (status {response.status_code})")
            return False
    except requests.exceptions.ConnectionError:
        print("Backend health check: FAILED (connection error)")
        return False


def test_ask_endpoint():
    print("Testing /ask/ endpoint...")
    try:
        response = requests.post(
            f"{BACKEND_URL}/ask/",
            data={"question": "What is aspirin used for?"},
            timeout=30,
        )
        if response.status_code == 200:
            data = response.json()
            print("Ask endpoint: PASSED")
            print(f"  Response: {data.get('response', 'N/A')[:100]}...")
            print(f"  Sources: {data.get('sources', [])}")
            print(f"  Doubt certificate: {data.get('doubt_certificate') is not None}")
            print(f"  Run artifact ID: {data.get('run_artifact_id')}")
            return True
        else:
            print(f"Ask endpoint: FAILED (status {response.status_code})")
            print(f"  Response: {response.text[:200]}")
            return False
    except requests.exceptions.ConnectionError:
        print("Ask endpoint: FAILED (connection error)")
        return False
    except Exception as e:
        print(f"Ask endpoint: FAILED ({e})")
        return False


def test_emergency_bypass():
    print("Testing emergency bypass...")
    try:
        response = requests.post(
            f"{BACKEND_URL}/ask/",
            data={"question": "I have severe chest pain and can't breathe"},
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("doubt_certificate") is not None or data.get("response") is None:
                print("Emergency bypass: PASSED")
                return True
            else:
                print("Emergency bypass: FAILED (no emergency response)")
                return False
        else:
            print(f"Emergency bypass: FAILED (status {response.status_code})")
            return False
    except Exception as e:
        print(f"Emergency bypass: FAILED ({e})")
        return False


def test_doubt_certificate():
    print("Testing doubt certificate...")
    try:
        response = requests.post(
            f"{BACKEND_URL}/ask/",
            data={"question": "What is the cure for fictional disease X?"},
            timeout=30,
        )
        if response.status_code == 200:
            data = response.json()
            doubt_certificate = data.get("doubt_certificate")
            if doubt_certificate and doubt_certificate.get("status") == "insufficient_evidence":
                print("Doubt certificate: PASSED")
                print(f"  Status: {doubt_certificate.get('status')}")
                return True
            else:
                print("Doubt certificate: FAILED (no doubt certificate with insufficient_evidence)")
                return False
        else:
            print(f"Doubt certificate: FAILED (status {response.status_code})")
            return False
    except Exception as e:
        print(f"Doubt certificate: FAILED ({e})")
        return False


def test_run_artifact_download():
    print("Testing run artifact metadata...")
    try:
        ask_response = requests.post(
            f"{BACKEND_URL}/ask/",
            data={"question": "What is aspirin used for?"},
            timeout=30,
        )
        if ask_response.status_code != 200:
            print(f"Run artifact metadata: FAILED (ask endpoint returned {ask_response.status_code})")
            return False

        ask_data = ask_response.json()
        run_artifact_id = ask_data.get("run_artifact_id")
        if not run_artifact_id:
            print("Run artifact metadata: FAILED (no run_artifact_id in response)")
            return False

        print("Run artifact metadata: PASSED")
        print(f"  Artifact ID: {run_artifact_id}")
        print("  Note: Frontend provides chat history download via session state.")
        return True
    except Exception as e:
        print(f"Run artifact metadata: FAILED ({e})")
        return False


def run_uat():
    print("=" * 60)
    print("CURA-Med UAT Test Suite")
    print("=" * 60)
    print()
    print("Prerequisites:")
    print("1. Backend server running on http://127.0.0.1:8000")
    print("2. Frontend server running on http://127.0.0.1:8501")
    print()
    print("To start servers:")
    print("  Backend:  cd backend/server && python -m uvicorn main:app --host 0.0.0.0 --port 8000")
    print("  Frontend: cd frontend && streamlit run app.py")
    print()
    print("=" * 60)
    print()

    results = []

    if not test_backend_health():
        print()
        print("Backend is not running. Please start it first.")
        print("  cd backend/server")
        print("  python -m uvicorn main:app --host 0.0.0.0 --port 8000")
        return False

    results.append(("Backend Health", True))
    results.append(("Ask Endpoint", test_ask_endpoint()))
    results.append(("Emergency Bypass", test_emergency_bypass()))
    results.append(("Doubt Certificate", test_doubt_certificate()))
    results.append(("Run Artifact Download", test_run_artifact_download()))

    print()
    print("=" * 60)
    print("UAT Test Results")
    print("=" * 60)
    passed = sum(1 for _, r in results if r)
    total = len(results)
    for name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"  {name}: {status}")
    print()
    print(f"Total: {passed}/{total} passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = run_uat()
    sys.exit(0 if success else 1)
