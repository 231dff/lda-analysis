#!/bin/bash
# ============================================================
# LDA Docker Entrypoint Script
# ============================================================
# Generates .streamlit/secrets.toml from environment variables
# at container startup, then launches Streamlit.
# ============================================================

set -e

SECRETS_FILE="/app/.streamlit/secrets.toml"

echo "🔧 Configuring LDA..."

# Check required environment variables
if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_KEY" ] || [ -z "$GROQ_API_KEY" ]; then
    echo "❌ ERROR: Missing required environment variables."
    echo "   Required: SUPABASE_URL, SUPABASE_KEY, GROQ_API_KEY"
    echo ""
    echo "   Set them in your .env file or pass them to docker:"
    echo "   docker run -e SUPABASE_URL=... -e SUPABASE_KEY=... -e GROQ_API_KEY=... lda"
    exit 1
fi

echo "📝 Generating Streamlit secrets from environment variables..."
cat > "$SECRETS_FILE" << EOF
# Auto-generated from environment variables — do not edit manually
SUPABASE_URL = "${SUPABASE_URL}"
SUPABASE_KEY = "${SUPABASE_KEY}"
GROQ_API_KEY = "${GROQ_API_KEY}"
EOF

echo "✅ Secrets configured"
echo "🚀 Starting LDA on http://0.0.0.0:${STREAMLIT_SERVER_PORT:-8501}"

# Execute Streamlit
exec streamlit run src/main.py \
    --server.port="${STREAMLIT_SERVER_PORT:-8501}" \
    --server.address="${STREAMLIT_SERVER_ADDRESS:-0.0.0.0}" \
    --server.headless=true \
    --browser.gatherUsageStats=false \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false
