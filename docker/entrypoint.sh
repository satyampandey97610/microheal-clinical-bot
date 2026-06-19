#!/bin/bash
set -euo pipefail

UI_PORT="${STREAMLIT_INTERNAL_PORT:-8502}"
PUBLIC_PORT="${PORT:-8501}"

streamlit run app.py \
  --server.port="${UI_PORT}" \
  --server.address=127.0.0.1 \
  --server.headless=true \
  --server.enableCORS=false \
  --server.enableXsrfProtection=false &
STREAMLIT_PID=$!

cleanup() {
  kill "${STREAMLIT_PID}" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup SIGTERM SIGINT

for _ in $(seq 1 45); do
  if python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:${UI_PORT}/_stcore/health')" 2>/dev/null; then
    break
  fi
  sleep 1
done

# Copy nginx config
cp nginx.conf /etc/nginx/nginx.conf

# Run API in background
uvicorn api:app --host 127.0.0.1 --port 8000 &

# Start Nginx in foreground
exec nginx -g 'daemon off;'
