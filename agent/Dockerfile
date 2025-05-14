# ─────────────────── agent/Dockerfile ───────────────────
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

# Install build dependencies required for sentence-transformers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY agent/requirements.txt .
RUN pip install -r requirements.txt

# copy source
COPY agent .

# 🟢 pull the model weights and sentence-transformer models once, at build‑time
RUN python main.py download-files \
    && echo "Turn‑detector weights downloaded." \
    && python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')" \
    && echo "Sentence-transformer model downloaded."

# Make the entrypoint script executable
RUN chmod +x docker-entrypoint.sh

# Create volume for MongoDB data persistence
VOLUME /data/db

EXPOSE 8000
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["dev"]
