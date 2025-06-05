# Simple Streamlit UI for Multi-Agent System
import streamlit as st
import os
from main import main_pipeline
from shared_memory import load_memory
import sys

st.title("Multi-Agent AI System Demo")

st.header("Upload Input (Email, JSON, PDF)")
uploaded_file = st.file_uploader("Choose a file", type=["txt", "json", "pdf", "eml"])

if uploaded_file:
    uploads_dir = os.path.join(os.path.dirname(__file__), 'uploads')
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
    file_path = os.path.join(uploads_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"File uploaded to: {file_path}")
    # Simulate CLI run with the uploaded file
    sys.argv = [sys.argv[0], '--input_file', file_path]
    with st.spinner("Processing..."):
        main_pipeline()
    # Show summary for this input
    memory = load_memory()
    latest_entry = None
    for entry in reversed(memory.get('results', [])):
        entry_id = entry['input_meta'].get('source') or 'user_input_email'
        if entry_id == file_path:
            latest_entry = entry
            break
    st.header("Agent Summary for This Input")
    if latest_entry:
        st.write(f"Timestamp: {latest_entry['timestamp']}")
        st.write(f"Agent: {latest_entry['agent']}")
        st.write(f"Input: {latest_entry['input_meta']}")
        st.write(f"Extracted: {latest_entry['extracted']}")
        st.write(f"Actions: {latest_entry['actions']}")
        st.write(f"Trace: {latest_entry['trace']}")
    else:
        st.warning("No summary found for this input.")

st.header("View Routing & Memory Log")
if st.button("Show Memory Log"):
    memory = load_memory()
    st.json(memory)
