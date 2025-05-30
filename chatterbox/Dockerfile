# Dockerfile for Chatterbox TTS service
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for OpenMP and audio I/O
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libsndfile1 \
&& rm -rf /var/lib/apt/lists/*

# Increase pip timeout and upgrade pip
ENV PIP_DEFAULT_TIMEOUT=100
RUN pip install --no-cache-dir --upgrade pip

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Expose service port
EXPOSE 8001

# Run the FastAPI application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"] 