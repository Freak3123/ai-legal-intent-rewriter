# Dockerfile for Hugging Face Spaces (Docker SDK, free CPU tier)
# Spaces expects the app to listen on port 7860.

FROM python:3.11-slim

# System deps:
# - tesseract-ocr: needed for the OCR fallback path on scanned PDFs
# - build-essential: needed by some Python packages with C extensions
# - curl: needed by the uv installer
# - libgl1, libglib2.0-0: required by PyMuPDF in some scanned-PDF code paths
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    build-essential \
    curl \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install uv (fast Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml ./
COPY uv.lock* ./

# Install Python deps into a venv inside the image
RUN uv sync --frozen --no-dev || uv sync --no-dev

# Download spaCy model used by NER. Cached as a Docker layer so rebuilds are fast.
RUN uv run python -m spacy download en_core_web_sm

# Copy application code
COPY app/ ./app/

# HF Spaces expects port 7860
EXPOSE 7860

# HF Spaces sets HOME to /home/user; cache HF downloads there
ENV HF_HOME=/tmp/huggingface
ENV TRANSFORMERS_CACHE=/tmp/huggingface

# Run the app
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
