import streamlit as st
import pandas as pd

from assistant.analyzer import analyze_email
from assistant.guardrails import check_request
from config import MODEL_NAME

st.set_page_config(page_title="Grounded Phishing Assistant", page_icon="🛡️", layout="wide")

st.title("🛡️ Grounded AI Phishing Email Security Assistant")
st.caption("A scoped assistant that analyzes email evidence, applies guardrails, and tracks token usage.")

with st.sidebar:
    st.header("Project information")
    st.write(f"**Model:** `{MODEL_NAME}`")
    st.write("**Scope:** Email phishing and security analysis")
    st.info("Do not paste real passwords, OTPs, private keys, or sensitive personal information.")
    st.caption("AI results are advisory. Verify suspicious messages through a trusted channel.")

st.subheader("1. Request")
request = st.text_input(
    "What should the assistant do?",
    value="Analyze this email for phishing and explain the evidence."
)

st.subheader("2. Email to inspect")
email_text = st.text_area(
    "Paste the complete email (sender, subject, body, links if available)",
    height=240,
    placeholder="From: support@example.com\nSubject: Verify your account\n\nDear customer..."
)

if st.button("Analyze email", type="primary", use_container_width=True):
    decision = check_request(request)

    if not decision.allowed:
        st.error(decision.message)
        st.stop()

    if len(email_text.strip()) < 15:
        st.warning("Please paste an email with at least 15 characters.")
        st.stop()

    with st.spinner("Analyzing the email..."):
        try:
            result, usage = analyze_email(email_text)
        except Exception as exc:
            st.error(f"Analysis failed: {exc}")
            st.stop()

    category = result["classification"]
    if category == "PHISHING":
        st.error(f"Classification: {category}")
    elif category == "SAFE":
        st.success(f"Classification: {category}")
    else:
        st.warning(f"Classification: {category}")

    st.write(f"**Risk level:** {result['risk_level']}")
    st.write(f"**Summary:** {result['summary']}")

    st.subheader("Evidence found in the email")
    if result["evidence"]:
        for item in result["evidence"]:
            st.markdown(f"- **{item['indicator']}** — “{item['quote']}”")
    else:
        st.write("No direct evidence excerpts were returned.")

    st.subheader("Recommended action")
    st.write(result["recommended_action"])

    if result.get("limitations"):
        st.subheader("Limitations")
        for item in result["limitations"]:
            st.markdown(f"- {item}")

    st.subheader("Usage and estimated cost")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Input tokens", usage["input_tokens"])
    c2.metric("Output tokens", usage["output_tokens"])
    c3.metric("Total tokens", usage["total_tokens"])
    c4.metric("Estimated USD", f"${usage['estimated_cost_usd']:.8f}")
    st.caption(
        "Estimated paid-tier equivalent using the rates configured in config.py. "
        "This is not an invoice or a guarantee of actual billing."
    )

    with st.expander("View structured result"):
        st.json(result)

st.divider()
st.caption("Capstone project: guardrails + evidence-grounded analysis + scored evaluation + token/cost measurement.")
