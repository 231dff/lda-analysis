import streamlit as st
from config.prompts import LEGAL_SPECIALIST_PROMPTS
from utils.pdf_extractor import extract_text_from_pdf
from config.sample_data import SAMPLE_CONTRACT
from config.app_config import MAX_UPLOAD_SIZE_MB


def show_analysis_form():
    if (
        "current_session" in st.session_state
        and "report_source" not in st.session_state
    ):
        st.session_state.report_source = "Upload PDF"

    report_source = st.radio(
        "Choose document source",
        ["Upload PDF", "Use Sample Contract"],
        index=0 if st.session_state.get("report_source") == "Upload PDF" else 1,
        horizontal=True,
        key="report_source",
    )

    pdf_contents = get_document_contents(report_source)

    if pdf_contents:
        render_analysis_form(pdf_contents)


def get_document_contents(report_source):
    if report_source == "Upload PDF":
        uploaded_file = st.file_uploader(
            f"Upload legal document PDF (Max {MAX_UPLOAD_SIZE_MB}MB)",
            type=["pdf"],
            help=f"Maximum file size: {MAX_UPLOAD_SIZE_MB}MB. Only PDF files containing legal documents are supported",
        )
        if uploaded_file:
            file_size_mb = uploaded_file.size / (1024 * 1024)
            if file_size_mb > MAX_UPLOAD_SIZE_MB:
                st.error(
                    f"File size ({file_size_mb:.1f}MB) exceeds the {MAX_UPLOAD_SIZE_MB}MB limit."
                )
                return None

            if uploaded_file.type != "application/pdf":
                st.error("Please upload a valid PDF file.")
                return None

            pdf_contents = extract_text_from_pdf(uploaded_file)
            if isinstance(pdf_contents, str) and (
                pdf_contents.startswith(
                    ("File size exceeds", "Invalid file type", "Error validating")
                )
                or pdf_contents.startswith("The uploaded file")
                or "error" in pdf_contents.lower()
            ):
                st.error(pdf_contents)
                return None
            with st.expander("View Extracted Document"):
                st.text(pdf_contents)
            return pdf_contents
    else:
        with st.expander("View Sample Contract"):
            st.text(SAMPLE_CONTRACT)
        return SAMPLE_CONTRACT
    return None


def render_analysis_form(pdf_contents):
    with st.form("analysis_form"):
        party_name = st.text_input("Party / Entity Name")
        col1, col2 = st.columns(2)
        with col1:
            doc_type = st.selectbox(
                "Document Type",
                [
                    "Service Agreement",
                    "Non-Disclosure Agreement",
                    "Employment Contract",
                    "Lease Agreement",
                    "License Agreement",
                    "Partnership Agreement",
                    "Sales Contract",
                    "Settlement Agreement",
                    "Terms of Service",
                    "Other Legal Document",
                ],
            )
        with col2:
            jurisdiction = st.selectbox(
                "Governing Jurisdiction",
                [
                    "California",
                    "Delaware",
                    "New York",
                    "Texas",
                    "Florida",
                    "England & Wales",
                    "EU/GDPR",
                    "Singapore",
                    "Hong Kong",
                    "Other",
                ],
            )

        if st.form_submit_button("Analyze Document"):
            handle_form_submission(party_name, doc_type, jurisdiction, pdf_contents)


def handle_form_submission(party_name, doc_type, jurisdiction, pdf_contents):
    if not all([party_name, doc_type, jurisdiction]):
        st.error("Please fill in all fields")
        return

    from services.ai_service import generate_analysis

    can_analyze, error_msg = generate_analysis(None, None, check_only=True)
    if not can_analyze:
        st.error(error_msg)
        st.stop()
        return

    with st.spinner("Analyzing legal document..."):
        st.session_state.current_document_text = pdf_contents

        st.session_state.auth_service.save_chat_message(
            st.session_state.current_session["id"],
            f"Analyzing {doc_type} for party: {party_name}",
        )

        result = generate_analysis(
            {
                "party_name": party_name,
                "doc_type": doc_type,
                "jurisdiction": jurisdiction,
                "document": pdf_contents,
            },
            LEGAL_SPECIALIST_PROMPTS["comprehensive_analyst"],
        )

        if result["success"]:
            document_metadata = f"__DOCUMENT_TEXT__\n{pdf_contents}\n__END_DOCUMENT_TEXT__"
            st.session_state.auth_service.save_chat_message(
                st.session_state.current_session["id"], document_metadata, role="system"
            )

            content = result["content"]
            if "model_used" in result:
                model_info = f"\n\n*Analysis generated using {result['model_used']}*"
                content += model_info

            st.session_state.auth_service.save_chat_message(
                st.session_state.current_session["id"], content, role="assistant"
            )
            st.rerun()
        else:
            st.error(result["error"])
            st.stop()
