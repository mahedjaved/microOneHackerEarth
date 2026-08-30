import os
import subprocess
import time
import pytest
import requests
from playwright.sync_api import sync_playwright, Page, Browser

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:8501")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


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
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def page(browser: Browser):
    page = browser.new_page()
    yield page
    page.close()


@pytest.fixture
def sample_pdf(tmp_path):
    """Create a minimal valid PDF file for testing."""
    pdf_path = tmp_path / "test_document.pdf"
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 68 >>
stream
BT
/F1 12 Tf
100 700 Td
(Aspirin is used for pain relief and reducing inflammation.) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000212 00000 n
trailer
<< /Size 5 /Root 1 0 R >>
startxref
331
%%EOF"""
    pdf_path.write_bytes(pdf_content)
    return str(pdf_path)


@pytest.fixture
def large_file(tmp_path):
    """Create a file exceeding 50MB."""
    large_path = tmp_path / "large_file.pdf"
    large_path.write_bytes(b"x" * (51 * 1024 * 1024))
    return str(large_path)
