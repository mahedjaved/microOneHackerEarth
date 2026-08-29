import streamlit as st
from utils import upload_pdfs_api


MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50MB


def render_upload():
    st.sidebar.subheader("📁 Upload Medical Documents (.pdf)")
    uploaded_files = st.sidebar.file_uploader(
        "Upload multiple PDF files", type="pdf", accept_multiple_files=True
    )
    if st.sidebar.button("Upload DB") and uploaded_files:
        oversize = [f.name for f in uploaded_files if f.size > MAX_FILE_SIZE_BYTES]
        if oversize:
            st.sidebar.error(
                f"File(s) exceed 50MB limit: {', '.join(oversize)}. Please reduce file size."
            )
            return
        response = upload_pdfs_api(uploaded_files)
        if response.status_code == 200:
            st.sidebar.success("Files uploaded successfully!")
        else:
            st.sidebar.error(f"Upload failed: {response.text}")
