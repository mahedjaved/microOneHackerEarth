import pytest
import requests
import time

BACKEND_URL = "http://127.0.0.1:8000"


@pytest.fixture(scope="session")
def backend_health():
    """Verify backend is healthy before running tests."""
    for _ in range(30):
        try:
            r = requests.get(f"{BACKEND_URL}/health", timeout=5)
            if r.status_code == 200:
                return r.json()
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    pytest.fail("Backend not available")
