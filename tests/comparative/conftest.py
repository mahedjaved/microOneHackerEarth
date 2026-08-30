import pytest
import requests
import time
import os

BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:8501"


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


@pytest.fixture(scope="session")
def frontend_health():
    """Verify frontend is healthy before running tests."""
    for _ in range(30):
        try:
            r = requests.get(f"{FRONTEND_URL}", timeout=5)
            if r.status_code == 200:
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    pytest.fail("Frontend not available")


@pytest.fixture(scope="session")
def results_dir():
    """Ensure results directory exists."""
    os.makedirs("tests/comparative/results", exist_ok=True)
    return "tests/comparative/results"


@pytest.fixture
def ask_system():
    """Factory fixture for asking questions to systems."""
    def _ask_system(system_endpoint, question, timeout=60):
        response = requests.post(
            system_endpoint,
            data={"question": question},
            timeout=timeout,
        )
        return response
    return _ask_system


@pytest.fixture
def mock_empty_corpus():
    """Simulate empty corpus scenario."""
    with patch("tests.comparative.test_dataset.TEST_QUESTIONS", []):
        yield


@pytest.fixture
def mock_pinecone_unavailable():
    """Simulate Pinecone unavailable scenario."""
    import backend.server.routes.medrag_baseline as medrag_module
    original_index = None

    class MockIndex:
        def query(self, *args, **kwargs):
            raise Exception("Pinecone unavailable")

    with patch.object(medrag_module, "Pinecone") as mock_pc:
        mock_pc.return_value.Index.return_value = MockIndex()
        yield


@pytest.fixture
def mock_rate_limit():
    """Simulate rate limit scenario."""
    import backend.server.routes.medrag_baseline as medrag_module
    import backend.server.routes.no_rag as no_rag_module

    class MockResponse:
        def invoke(self, *args, **kwargs):
            raise Exception("Rate limit exceeded")

    with patch.object(medrag_module, "ChatGroq") as mock_groq:
        mock_groq.return_value.invoke.side_effect = Exception("Rate limit exceeded")
        with patch.object(no_rag_module, "ChatGroq") as mock_groq2:
            mock_groq2.return_value.invoke.side_effect = Exception("Rate limit exceeded")
            yield
