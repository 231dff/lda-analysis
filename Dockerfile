# ============================================================
# Stage 1: Base Python image with system dependencies
# ============================================================
FROM python:3.11-slim-bookworm AS base

# System dependencies for FAISS, PDFPlumber, and sentence-transformers
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libopenblas0 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r streamlit && useradd -r -g streamlit -m -d /home/streamlit streamlit

# ============================================================
# Stage 2: Python dependencies
# ============================================================
FROM base AS dependencies

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================================
# Stage 3: Runtime
# ============================================================
FROM dependencies AS runtime

WORKDIR /app

# Copy application code
COPY src/ ./src/
COPY public/ ./public/
COPY .streamlit/ ./.streamlit/

# Create directories for persistent data
RUN mkdir -p /app/data/faiss_index /app/data/model_cache && \
    chown -R streamlit:streamlit /app

# Pre-download the HuggingFace sentence-transformers model
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2', cache_folder='/app/data/model_cache')"

# Switch to non-root user
USER streamlit

# Streamlit default port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Environment variable defaults
ENV STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    HF_HOME=/app/data/model_cache \
    SENTENCE_TRANSFORMERS_HOME=/app/data/model_cache

# Copy entrypoint script and make executable
COPY --chown=streamlit:streamlit docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

ENTRYPOINT ["/app/docker-entrypoint.sh"]
