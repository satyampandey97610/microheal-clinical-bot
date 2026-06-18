#!/bin/bash
set -euo pipefail

UI_PORT="${STREAMLIT_INTERNAL_PORT:-8502}"
PUBLIC_PORT="${PORT:-8501}"

streamlit run app.py \
  --server.port="${UI_PORT}" \
  --server.address=127.0.0.1 \
  --server.headless=true &
STREAMLIT_PID=$!

cleanup() {
  kill "${STREAMLIT_PID}" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup SIGTERM SIGINT

for _ in $(seq 1 45); do
  if curl -sf "http://127.0.0.1:${UI_PORT}/_stcore/health" >/dev/null; then
    break
  fi
  sleep 1
done

exec uvicorn server:app --host 0.0.0.0 --port "${PUBLIC_PORT}"
