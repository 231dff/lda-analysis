# ⚖️ LDA (Legal Document Analyzer)

AI Agent to analyze legal documents, contracts, and agreements — providing detailed legal risk assessments and insights.

<p align="center">
  <a href="#-features">Features</a> |
  <a href="#%EF%B8%8F-tech-stack">Tech Stack</a> |
  <a href="#-installation">Installation</a> |
  <a href="#-project-structure">Project Structure</a>
</p>

## 🌟 Features

- **Agent-based architecture**
  - **Analysis Agent**: Document analysis with in-context learning from previous analyses and a built-in knowledge base
  - **Chat Agent**: RAG-powered follow-up Q&A over your document (FAISS + HuggingFace embeddings)
- **Multi-model cascade** via Groq with automatic fallback (primary → secondary → tertiary → fallback)
- **Chat sessions**: Create multiple analysis sessions; each session stores document, analysis, and follow-up messages in Supabase
- **Document sources**: Upload your own PDF or use the built-in sample contract for quick testing
- **PDF handling**: Upload up to 20MB, max 50 pages; validation for file type and legal-document content
- **Daily analysis limit**: Configurable cap (default 15/day) with countdown in the sidebar
- **Secure auth**: Supabase Auth (sign up / sign in), session validation, and configurable session timeout
- **Session history**: View, switch, and delete past sessions; document text persisted for follow-up chat across reloads
- **Modern UI**: Responsive Streamlit app with sidebar session list, user greeting, and real-time feedback

## 🛠️ Tech Stack

- **Frontend**: Streamlit (1.42+)
- **AI / LLM**
  - **Document analysis**: Groq with multi-model fallback via `ModelManager`
    - Primary: `meta-llama/llama-4-maverick-17b-128e-instruct`
    - Secondary: `llama-3.3-70b-versatile`
    - Tertiary: `llama-3.1-8b-instant`
    - Fallback: `llama3-70b-8192`
  - **Follow-up chat**: RAG with LangChain, HuggingFace embeddings (`all-MiniLM-L6-v2`), FAISS vector store, and Groq (`llama-3.3-70b-versatile`)
- **Database**: Supabase (PostgreSQL)
  - Tables: `users`, `chat_sessions`, `chat_messages`
- **Auth**: Supabase Auth, Gotrue
- **PDF**: PDFPlumber (text extraction), filetype (file validation)
- **Libraries**: LangChain, LangChain Community, LangChain HuggingFace, LangChain Text Splitters, sentence-transformers, FAISS (CPU)

## 🚀 Installation

#### Requirements 📋

- Python 3.8+
- Streamlit 1.42+
- Supabase account
- Groq API key
- PDFPlumber, filetype

#### Getting Started 📝

1. Clone the repository:

```bash
git clone https://github.com/yourusername/lda.git
cd lda
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Required environment variables (in `.streamlit/secrets.toml`):

```toml
SUPABASE_URL = "your-supabase-url"
SUPABASE_KEY = "your-supabase-key"
GROQ_API_KEY = "your-groq-api-key"
```

4. Set up Supabase database schema:

The application uses three tables: `users`, `chat_sessions`, and `chat_messages`. Use the SQL script at `public/db/script.sql` to create them.

(You can turn off email confirmation on signup in Supabase: **Authentication → Providers → Email → Confirm email**.)

5. Run the application:

```bash
streamlit run src/main.py
```

## 📁 Project Structure

```
lda/
├── requirements.txt
├── README.md
├── src/
│   ├── main.py                 # Application entry point; chat UI and session flow
│   ├── auth/
│   │   ├── auth_service.py     # Supabase auth, sessions, chat message persistence
│   │   └── session_manager.py  # Session init, timeout, create/delete chat sessions
│   ├── components/
│   │   ├── analysis_form.py    # Document source (upload/sample), analysis form, analysis trigger
│   │   ├── auth_pages.py       # Login / signup pages
│   │   ├── footer.py           # Footer component
│   │   ├── header.py           # User greeting
│   │   └── sidebar.py          # Session list, new session, daily limit, logout
│   ├── config/
│   │   ├── app_config.py       # App name, limits (upload, pages, analysis, timeout)
│   │   ├── prompts.py          # Legal specialist prompts for document analysis
│   │   └── sample_data.py      # Sample legal contract for "Use Sample Contract"
│   ├── services/
│   │   └── ai_service.py       # Analysis + chat entry points; vector store caching
│   ├── agents/
│   │   ├── analysis_agent.py   # Document analysis, rate limits, knowledge base, in-context learning
│   │   ├── chat_agent.py       # RAG pipeline (embeddings, FAISS, query contextualization)
│   │   └── model_manager.py    # Groq multi-model cascade and fallback
│   └── utils/
│       ├── validators.py       # Email, password, PDF file and content validation
│       └── pdf_extractor.py    # PDF text extraction and validation
├── public/
│   └── db/
│       ├── script.sql          # Supabase schema (users, chat_sessions, chat_messages)
└── .streamlit/
    └── config.toml             # Streamlit theme and server configuration
```

## 📄 License

This project is licensed under the MIT License.
