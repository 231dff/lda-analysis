import streamlit as st
from agents.analysis_agent import AnalysisAgent


def init_analysis_state():
    """Initialize analysis-related session state variables."""
    if "analysis_agent" not in st.session_state:
        st.session_state.analysis_agent = AnalysisAgent()

    if "chat_agent" not in st.session_state:
        try:
            from agents.chat_agent import ChatAgent

            if "GROQ_API_KEY" not in st.secrets:
                st.session_state.chat_agent = None
                st.session_state.chat_agent_error = "GROQ_API_KEY not found in secrets. Please add it to .streamlit/secrets.toml"
            else:
                st.session_state.chat_agent = ChatAgent()
                st.session_state.chat_agent_error = None
        except KeyError as e:
            st.session_state.chat_agent = None
            st.session_state.chat_agent_error = f"Missing configuration: {str(e)}. Please check your .streamlit/secrets.toml file."
        except ImportError as e:
            st.session_state.chat_agent = None
            st.session_state.chat_agent_error = (
                f"Missing dependencies: {str(e)}. Please install required packages."
            )
        except Exception as e:
            st.session_state.chat_agent = None
            import traceback

            error_details = traceback.format_exc()
            st.session_state.chat_agent_error = f"Failed to initialize chat agent: {str(e)}\n\nDetails: {error_details[:500]}"


def check_rate_limit():
    init_analysis_state()
    return st.session_state.analysis_agent.check_rate_limit()


def generate_analysis(data, system_prompt, check_only=False, session_id=None):
    """Generate analysis if within rate limits."""
    init_analysis_state()

    if check_only:
        return st.session_state.analysis_agent.check_rate_limit()

    return st.session_state.analysis_agent.analyze_report(
        data=data, system_prompt=system_prompt, check_only=False
    )


def get_chat_response(query, context_text, chat_history):
    """Generate chat response using RAG."""
    init_analysis_state()

    if st.session_state.chat_agent is None:
        error_msg = st.session_state.get(
            "chat_agent_error",
            "Chat functionality is currently unavailable. Please check your GROQ_API_KEY configuration in .streamlit/secrets.toml",
        )
        return f"Error: {error_msg}"

    if not context_text and chat_history:
        for msg in chat_history:
            if msg.get("role") == "system" and "__DOCUMENT_TEXT__" in msg.get(
                "content", ""
            ):
                content = msg.get("content", "")
                start_idx = content.find("__DOCUMENT_TEXT__\n") + len("__DOCUMENT_TEXT__\n")
                end_idx = content.find("\n__END_DOCUMENT_TEXT__")
                if start_idx > len("__DOCUMENT_TEXT__\n") - 1 and end_idx > start_idx:
                    context_text = content[start_idx:end_idx]
                    break

        if not context_text:
            for msg in reversed(chat_history):
                if msg["role"] == "assistant" and len(msg.get("content", "")) > 100:
                    context_text = msg["content"][:5000]
                    break

    if not context_text:
        context_text = "No document context available. Relying on chat history only."

    if "vector_store" not in st.session_state or st.session_state.get(
        "vector_store_key"
    ) != len(context_text):
        try:
            with st.spinner("Processing context..."):
                st.session_state.vector_store = (
                    st.session_state.chat_agent.initialize_vector_store(context_text)
                )
                st.session_state.vector_store_key = len(context_text)
        except Exception as e:
            st.warning(
                f"Could not create vector store: {str(e)}. Using chat history only."
            )
            try:
                st.session_state.vector_store = (
                    st.session_state.chat_agent.initialize_vector_store(
                        "No document context available."
                    )
                )
                st.session_state.vector_store_key = 0
            except Exception:
                return f"Error: Could not initialize vector store. {str(e)}"

    return st.session_state.chat_agent.get_response(
        query, st.session_state.vector_store, chat_history
    )
