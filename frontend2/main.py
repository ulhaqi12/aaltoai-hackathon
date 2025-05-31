import streamlit as st
import requests

# Page setup
st.set_page_config(page_title="Khawarizmi", layout="centered")

# --- Modern white theme CSS ---
st.markdown("""
<style>
html, body {
    background-color: #f4f6f8;
    font-family: 'Inter', sans-serif;
}
h1, h2 {
    color: #1f2937;
}
.stTextInput>div>div>input {
    border-radius: 8px;
    padding: 0.6rem 0.75rem;
    border: 1px solid #d1d5db;
    background-color: #ffffff;
    color: #111827;
}
.stButton>button {
    background-color: #3b82f6;
    color: white;
    font-weight: 500;
    border-radius: 6px;
    padding: 0.6rem 1.2rem;
    transition: background 0.2s;
}
.stButton>button:hover {
    background-color: #2563eb;
}
.report-box {
    background-color: white;
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.05);
    margin-top: 2rem;
}
</style>
""", unsafe_allow_html=True)

# --- Header Section ---
st.markdown("### 📊 Khawarizmi")
st.markdown("Ask questions in plain English and get insightful SQL-powered charts.")

# --- Input field ---
intent = st.text_input("💡 Ask your question", placeholder="e.g., Show top 10 products by revenue")

# --- Submit Button ---
submit = st.button("🚀 Generate Report")

# --- Report Display Logic ---
if submit and intent.strip():
    with st.spinner("Generating report..."):
        try:
            response = requests.post(
                "http://localhost:8074/pipeline",
                json={"intent": intent, "model": "gpt-4o"}
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    html = data.get("html_report", "")
                    st.markdown('<div class="report-box">', unsafe_allow_html=True)
                    st.components.v1.html(html, height=800, scrolling=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.error("❌ Report generation failed: " + str(data))
            else:
                st.error(f"❌ HTTP {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"🚨 Error: {e}")
elif submit:
    st.warning("Please enter a question before submitting.")
