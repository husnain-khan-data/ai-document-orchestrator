
import streamlit as st
import requests
import json
import fitz  # PyMuPDF

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------
st.set_page_config(
    page_title="AI Document Orchestrator",
    page_icon="📄",
    layout="wide"
)

# ---------------------------------------------------
# TITLE
# ---------------------------------------------------
st.title("📄 AI-Powered Document Orchestrator")

st.markdown("""
Upload a document, ask analytical questions, extract structured insights using AI,
and trigger automated email alerts using n8n.
""")

# ---------------------------------------------------
# OPENROUTER API
# ---------------------------------------------------
OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]

# ---------------------------------------------------
# N8N WEBHOOK
# ---------------------------------------------------
N8N_WEBHOOK_URL = st.secrets["N8N_WEBHOOK_URL"]

# ---------------------------------------------------
# PDF TEXT EXTRACTION
# ---------------------------------------------------
def extract_text_from_pdf(pdf_file):

    text = ""

    pdf_document = fitz.open(
        stream=pdf_file.read(),
        filetype="pdf"
    )

    for page in pdf_document:
        text += page.get_text()

    return text


# ---------------------------------------------------
# TXT TEXT EXTRACTION
# ---------------------------------------------------
def extract_text_from_txt(txt_file):

    return txt_file.read().decode("utf-8")


# ---------------------------------------------------
# AI ANALYSIS FUNCTION
# ---------------------------------------------------
def analyze_document(document_text, user_question):

    prompt = f"""
    You are an AI document analyst.

    Analyze the document carefully.

    USER QUESTION:
    {user_question}

    DOCUMENT:
    {document_text}

    Return response ONLY in JSON format:

    {{
      "key_insights": {{
        "field_1": "",
        "field_2": "",
        "field_3": "",
        "field_4": "",
        "field_5": ""
      }},
      "final_answer": "",
      "email_summary": ""
    }}
    """

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload
    )

    result = response.json()

    ai_response = result["choices"][0]["message"]["content"]

    cleaned_response = ai_response.replace(
        "```json",
        ""
    ).replace(
        "```",
        ""
    ).strip()

    return json.loads(cleaned_response)


# ---------------------------------------------------
# FILE UPLOAD
# ---------------------------------------------------
uploaded_file = st.file_uploader(
    "📂 Upload PDF or TXT File",
    type=["pdf", "txt"]
)

# ---------------------------------------------------
# QUESTION INPUT
# ---------------------------------------------------
user_question = st.text_area(
    "❓ Ask Question About Document",
    placeholder="Example: Extract important business risks from this report."
)

# ---------------------------------------------------
# EMAIL INPUT
# ---------------------------------------------------
recipient_email = st.text_input(
    "📧 Recipient Email ID",
    placeholder="Enter recipient email"
)

# ---------------------------------------------------
# EMAIL CHECKBOX
# ---------------------------------------------------
send_email = st.checkbox("Send Automated Email Alert")

# ---------------------------------------------------
# ANALYZE BUTTON
# ---------------------------------------------------
if st.button("🚀 Analyze Document"):

    if uploaded_file is None:

        st.warning("Please upload a file.")

    elif user_question == "":

        st.warning("Please enter a question.")

    else:

        with st.spinner("Processing document..."):

            # ---------------------------------------------------
            # EXTRACT TEXT
            # ---------------------------------------------------
            if uploaded_file.type == "application/pdf":

                extracted_text = extract_text_from_pdf(uploaded_file)

            else:

                extracted_text = extract_text_from_txt(uploaded_file)

            # ---------------------------------------------------
            # AI ANALYSIS
            # ---------------------------------------------------
            try:

                result = analyze_document(
                    extracted_text,
                    user_question
                )

                # ---------------------------------------------------
                # OUTPUT 1
                # ---------------------------------------------------
                st.subheader("📌 Structured JSON Output")

                st.json(result["key_insights"])

                # ---------------------------------------------------
                # OUTPUT 2
                # ---------------------------------------------------
                st.subheader("🧠 Final Analytical Answer")

                st.write(result["final_answer"])

                # ---------------------------------------------------
                # OUTPUT 3
                # ---------------------------------------------------
                st.subheader("📧 Generated Email Summary")

                st.write(result["email_summary"])

                # ---------------------------------------------------
                # EMAIL AUTOMATION
                # ---------------------------------------------------
                if send_email:

                    payload = {
                        "email": recipient_email,
                        "question": user_question,
                        "answer": result["final_answer"],
                        "summary": result["email_summary"]
                    }

                    webhook_response = requests.post(
                        N8N_WEBHOOK_URL,
                        json=payload
                    )

                    if webhook_response.status_code == 200:

                        # ---------------------------------------------------
                        # OUTPUT 4
                        # ---------------------------------------------------
                        st.subheader("✅ Email Automation Status")

                        st.success("Alert Email Sent Successfully!")

                    else:

                        st.error("Failed to trigger email automation.")

                else:

                    st.info("Email automation not selected.")

            except Exception as e:

                st.error(f"Error: {e}")