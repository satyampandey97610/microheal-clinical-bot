<<<<<<< HEAD
# MicroHeal Clinical Bot - Octa-specialty Architecture
# Supports 8 Medical Specialties: Gastro, Cardio, Nephro, Neuro, Gyneco, Onco, Ortho, Geriatric
# Use the official lightweight Python image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (required for some Python packages like PyMuPDF)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port Streamlit runs on
EXPOSE 8501

# Run the Streamlit app
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
=======
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
>>>>>>> 848bcc72937d70826d927480a4dc9666f03d2386
