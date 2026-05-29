# Use a professional, slim Python base image
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GASTRO_RAG_RESULTS_DIR=/app/results \
    STREAMLIT_INTERNAL_PORT=8502 \
    PORT=8501

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x docker/entrypoint.sh

# Single server: FastAPI retrieval + Streamlit UI (proxied) on 8501
EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=3 \
  CMD curl --fail http://localhost:8501/health && curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["/app/docker/entrypoint.sh"]
