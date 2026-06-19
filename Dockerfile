# MicroHeal Clinical Bot - Octa-specialty Architecture
# Supports 8 Medical Specialties: Gastro, Cardio, Nephro, Neuro, Gyneco, Onco, Ortho, Geriatric
# Use the official lightweight Python image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (required for some Python packages like PyMuPDF)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

ENV STREAMLIT_INTERNAL_PORT=8502 \
    PORT=8501

# Copy the rest of the application code
COPY . .

RUN chmod +x docker/entrypoint.sh

# Single server: FastAPI retrieval + Streamlit UI (proxied) on 8501
EXPOSE 8501

# Run the Unified Server
ENTRYPOINT ["/app/docker/entrypoint.sh"]
