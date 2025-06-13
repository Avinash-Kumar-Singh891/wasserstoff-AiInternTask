import streamlit as st
import requests

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="Document Theme QA", layout="wide")
st.title("Document Research & Theme Identifier")
st.header("Upload Documents")

upload_mode = st.radio("Choose upload mode:", ["Single Document", "Batch Upload"])

if upload_mode == "Single Document":
    file = st.file_uploader("Upload a PDF or image file", type=["pdf", "png", "jpg","txt","md"])
    if file and st.button("Upload"):
        with st.spinner("Uploading..."):
            response = requests.post(
                f"{API_BASE}/upload",
                files={"file": (file.name, file.getvalue())}
            )
            if response.ok:
                st.success("File uploaded and processed successfully")
                st.json(response.json())
            else:
                st.error(response.text)
else:
    files = st.file_uploader("Upload multiple files", type=["pdf","png","jpg"],accept_multiple_files=True)
    if files and st.button("Upload All"):
        with st.spinner("Uploading batch"):
            form_files = [("files", (f.name, f.getvalue())) for f in files]
            response = requests.post(f"{API_BASE}/upload-batch", files=form_files)
            if response.ok:
                st.success("Batch upload completed")
                st.json(response.json())
            else:
                st.error(response.text)
st.header("Ask a Question")

question = st.text_input("Enter your question")

if st.button("Submit Question") and question.strip():
    with st.spinner("Processing"):
        response = requests.post(
            f"{API_BASE}/query",
            json={"question": question}
        )
        if response.ok:
            result = response.json()
            st.success("Response received")

            st.subheader("Synthesized Answer")
            st.markdown(result["synthesized_answer"])

            st.subheader("Themes with Citations ")
            for theme in result["themes"]:
                st.markdown(f"**{theme['name']}**")
                st.markdown(theme['summary'])

        else:
            st.error(response.text)
st.sidebar.header("Document Stats")
if st.sidebar.button("Refresh Stats"):
    response = requests.get(f"{API_BASE}/documents")
    if response.ok:
        stats = response.json()
        st.sidebar.metric("Documents", stats["total_documents"])
        st.sidebar.metric("Chunks", stats["total_chunks"])
    else:
        st.sidebar.error("Failed to load stats")
