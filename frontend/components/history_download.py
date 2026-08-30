import re
import streamlit as st
from datetime import datetime


PII_PATTERNS = [
    (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN REDACTED]'),
    (r'\b\d{10}\b', '[PHONE REDACTED]'),
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL REDACTED]'),
    (r'\b\d{1,2}/\d{1,2}/\d{4}\b', '[DOB REDACTED]'),
]


def _redact_pii(text: str) -> str:
    redacted = text
    for pattern, replacement in PII_PATTERNS:
        redacted = re.sub(pattern, replacement, redacted)
    return redacted


def render_history_download():
    if st.session_state.get("messages"):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        run_id = st.session_state.get('run_artifact_id', 'no-run-id')

        lines = [f"Run ID: {run_id}", f"Downloaded: {timestamp}", ""]
        for msg in st.session_state.messages:
            content = _redact_pii(msg['content'])
            lines.append(f"{msg['role'].upper()}: {content}")
            lines.append("")

        chat_text = "\n".join(lines)
        st.download_button(
            "Download Chat History",
            data=chat_text,
            file_name=f"chat_history_{run_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
        )
