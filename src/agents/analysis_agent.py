from datetime import datetime, timedelta
import streamlit as st
from agents.model_manager import ModelManager


class AnalysisAgent:
    """
    Agent responsible for managing document analysis, rate limiting,
    and implementing in-context learning from previous analyses.
    """

    def __init__(self):
        self.model_manager = ModelManager()
        self._init_state()

    def _init_state(self):
        """Initialize analysis-related session state variables."""
        if 'analysis_count' not in st.session_state:
            st.session_state.analysis_count = 0
        if 'last_analysis' not in st.session_state:
            st.session_state.last_analysis = datetime.now()
        if 'analysis_limit' not in st.session_state:
            st.session_state.analysis_limit = 15
        if 'models_used' not in st.session_state:
            st.session_state.models_used = {}
        if 'knowledge_base' not in st.session_state:
            st.session_state.knowledge_base = {}

    def check_rate_limit(self):
        """Check if user has reached their analysis limit."""
        time_until_reset = timedelta(days=1) - (datetime.now() - st.session_state.last_analysis)
        hours, remainder = divmod(time_until_reset.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        if time_until_reset.days < 0:
            st.session_state.analysis_count = 0
            st.session_state.last_analysis = datetime.now()
            return True, None

        if st.session_state.analysis_count >= st.session_state.analysis_limit:
            error_msg = f"Daily limit reached. Reset in {hours}h {minutes}m"
            return False, error_msg
        return True, None

    def analyze_report(self, data, system_prompt, check_only=False, chat_history=None):
        """
        Analyze document data using in-context learning from previous analyses.
        """
        can_analyze, error_msg = self.check_rate_limit()
        if not can_analyze:
            return {"success": False, "error": error_msg}

        if check_only:
            return can_analyze, error_msg

        processed_data = self._preprocess_data(data)

        enhanced_prompt = self._build_enhanced_prompt(system_prompt, processed_data, chat_history) if chat_history else system_prompt

        result = self.model_manager.generate_analysis(processed_data, enhanced_prompt)

        if result["success"]:
            self._update_analytics(result)
            self._update_knowledge_base(processed_data, result["content"])

        return result

    def _update_analytics(self, result):
        """Update analytics after successful analysis."""
        st.session_state.analysis_count += 1
        st.session_state.last_analysis = datetime.now()

        model_used = result.get("model_used", "unknown")
        if model_used in st.session_state.models_used:
            st.session_state.models_used[model_used] += 1
        else:
            st.session_state.models_used[model_used] = 1

    def _update_knowledge_base(self, data, analysis):
        """
        Update knowledge base with new analysis results for in-context learning.
        Maps key legal indicators to analysis patterns.
        """
        if not isinstance(data, dict) or 'document' not in data:
            return

        document_text = data['document'].lower()
        doc_type = data.get('doc_type', 'unknown')

        key_clauses = [
            "indemnification", "liability", "confidentiality",
            "termination", "governing law", "intellectual property",
            "warranty", "payment", "non-compete", "arbitration"
        ]

        for clause in key_clauses:
            if clause in document_text:
                if clause not in st.session_state.knowledge_base:
                    st.session_state.knowledge_base[clause] = {}

                if doc_type not in st.session_state.knowledge_base[clause]:
                    st.session_state.knowledge_base[clause][doc_type] = []

                lines = analysis.split('\n')
                relevant_lines = [l for l in lines if clause in l.lower()]
                if relevant_lines:
                    if len(st.session_state.knowledge_base[clause][doc_type]) >= 3:
                        st.session_state.knowledge_base[clause][doc_type].pop(0)
                    st.session_state.knowledge_base[clause][doc_type].append(relevant_lines[0])

    def _build_enhanced_prompt(self, system_prompt, data, chat_history):
        """
        Build an enhanced prompt using in-context learning from:
        1. Knowledge base of previous analyses
        2. Current session chat history
        """
        enhanced_prompt = system_prompt

        if isinstance(data, dict) and 'document' in data:
            kb_context = self._get_knowledge_base_context(data)
            if kb_context:
                enhanced_prompt += "\n\n## Relevant Learning From Previous Analyses\n" + kb_context

        if chat_history:
            session_context = self._get_session_context(chat_history)
            if session_context:
                enhanced_prompt += "\n\n## Current Session History\n" + session_context

        return enhanced_prompt

    def _get_knowledge_base_context(self, data):
        """Extract relevant context from knowledge base."""
        if 'knowledge_base' not in st.session_state or not st.session_state.knowledge_base:
            return ""

        document_text = data.get('document', '').lower()
        doc_type = data.get('doc_type', 'unknown')

        context_items = []

        for clause, doc_types in st.session_state.knowledge_base.items():
            if clause in document_text:
                if doc_type in doc_types:
                    for insight in doc_types[doc_type]:
                        context_items.append(f"- {clause} (similar document type): {insight}")

                for dtype, insights in doc_types.items():
                    if dtype != doc_type:
                        for insight in insights:
                            context_items.append(f"- {clause} (other document type): {insight}")

        if len(context_items) > 5:
            context_items = context_items[:5]

        return "\n".join(context_items) if context_items else ""

    def _get_session_context(self, chat_history):
        """Extract relevant context from current session."""
        if not chat_history or len(chat_history) < 2:
            return ""

        context_items = []
        for i in range(len(chat_history) - 1, 0, -2):
            if i >= 1 and chat_history[i-1]['role'] == 'user' and chat_history[i]['role'] == 'assistant':
                user_msg = chat_history[i-1]['content']
                ai_msg = chat_history[i]['content']

                if len(user_msg) > 200:
                    user_msg = user_msg[:197] + "..."
                if len(ai_msg) > 200:
                    ai_msg = ai_msg[:197] + "..."

                context_items.append(f"User: {user_msg}\nAssistant: {ai_msg}")

                if len(context_items) >= 2:
                    break

        return "\n\n".join(reversed(context_items)) if context_items else ""

    def _preprocess_data(self, data):
        """Pre-process data before sending to model."""
        if isinstance(data, dict):
            processed = {
                "party_name": data.get("party_name", ""),
                "doc_type": data.get("doc_type", ""),
                "jurisdiction": data.get("jurisdiction", ""),
                "document": data.get("document", "")
            }
            return processed
        return data
