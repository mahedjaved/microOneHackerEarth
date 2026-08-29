import os
import time
import requests
from config import API_URL


def _handle_response_error(response, context=""):
    try:
        detail = response.json().get("detail", response.text)
    except Exception:
        detail = response.text
    msg = f"{context} failed: {detail}" if context else f"Request failed: {detail}"
    raise RuntimeError(msg)


def _request_with_retry(method, url, retries=2, timeout=30, **kwargs):
    for attempt in range(1, retries + 1):
        try:
            response = requests.request(method, url, timeout=timeout, **kwargs)
            if response.status_code >= 500:
                if attempt < retries:
                    time.sleep(1 * attempt)
                    continue
            return response
        except requests.exceptions.ConnectionError as exc:
            if attempt < retries:
                time.sleep(1 * attempt)
                continue
            raise RuntimeError(f"Unable to connect to backend at {API_URL}.") from exc
        except requests.exceptions.Timeout as exc:
            if attempt < retries:
                time.sleep(1 * attempt)
                continue
            raise RuntimeError("Request timed out. Please try again.") from exc
    raise RuntimeError(f"{context or 'Request'} failed after {retries} retries.")


def is_backend_available():
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def upload_pdfs_api(files):
    files_payload = [("files", (f.name, f.read(), "application/pdf")) for f in files]
    response = _request_with_retry("POST", f"{API_URL}/upload_pdfs/", files=files_payload)
    if response.status_code != 200:
        _handle_response_error(response, context="Upload")
    return response


def ask_question(question, timeout=30):
    response = _request_with_retry(
        "POST",
        f"{API_URL}/ask/",
        data={"question": question},
        timeout=timeout,
    )
    if response.status_code != 200:
        _handle_response_error(response, context="Ask")
    return response
