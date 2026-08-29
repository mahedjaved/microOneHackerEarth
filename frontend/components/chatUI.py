import time
import streamlit as st
from config import API_URL
from utils import ask_question, is_backend_available


EMERGENCY_INSTRUCTION = (
    "If you are experiencing a medical emergency, please contact your local emergency services "
    "or go to the nearest emergency room immediately."
)


def _render_answer_block(answer, sources, disclaimer, doubt_certificate, run_artifact_id):
    if answer:
        st.chat_message("assistant").markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
    else:
        st.chat_message("assistant").markdown("No direct answer available from the approved evidence.")

    if disclaimer:
        st.info(disclaimer)

    if sources:
        st.caption("**Sources:** " + ", ".join(sources))

    if doubt_certificate:
        st.warning("**Doubt Certificate**")
        st.json(doubt_certificate)

    if run_artifact_id:
        st.caption(f"Run artifact ID: `{run_artifact_id}`")


def _render_emergency_response(response_text, disclaimer):
    st.error("**Emergency Safety Response**")
    st.markdown(response_text or EMERGENCY_INSTRUCTION)
    if disclaimer:
        st.info(disclaimer)


def _is_emergency_response(data):
    return bool(data.get("emergency") or "emergency" in (data.get("response") or "").lower())


def render_chat_ui():
    st.subheader("💬 Chat with your assistant")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if not is_backend_available():
        st.warning(
            "Backend is not available. Please ensure the server is running at "
            f"`{API_URL}`. Some features may be unavailable."
        )

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).markdown(msg["content"])

    user_input = st.chat_input("Type your question here ...")
    if user_input:
        st.chat_message("user").markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("assistant"):
            with st.spinner("Analyzing evidence ..."):
                start = time.time()
                try:
                    response = ask_question(user_input)
                except RuntimeError as exc:
                    st.error(str(exc))
                    return
                latency_ms = int((time.time() - start) * 1000)

            if response.status_code != 200:
                st.error(f"Error: {response.text}")
                return

            data = response.json()
            answer = data.get("response")
            sources = data.get("sources", [])
            disclaimer = data.get("disclaimer", "")
            doubt_certificate = data.get("doubt_certificate")
            run_artifact_id = data.get("run_artifact_id")

            if _is_emergency_response(data):
                _render_emergency_response(answer, disclaimer)
            else:
                _render_answer_block(answer, sources, disclaimer, doubt_certificate, run_artifact_id)

            st.caption(f"Response time: {latency_ms} ms")
