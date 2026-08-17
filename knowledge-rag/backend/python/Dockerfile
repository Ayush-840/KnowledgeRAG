# Knowledge RAG retrieval service — containerized for Render (or any Docker host).
#
# Notes:
# - CPU-only torch is installed first so requirements.txt never pulls the
#   multi-GB CUDA build.
# - sentence-transformers models (MiniLM embedder, bge-reranker) download on
#   first use into $HF_HOME. Point HF_HOME (and CHROMA_PERSISTENCE_DIR /
#   QUERY_LOG_DIR) at a persistent disk so data and model caches survive
#   restarts and deploys — see render.yaml at the repo root.
# - The 1.1 GB cross-encoder reranker is disabled by default here
#   (RERANKER_ENABLED=false); flip it on only on an instance with >= 2.5 GB RAM.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/data/hf-cache \
    CHROMA_PERSISTENCE_DIR=/data/chroma \
    QUERY_LOG_DIR=/data/logs \
    RERANKER_ENABLED=false

WORKDIR /srv

COPY requirements.txt .
RUN pip install --index-url https://download.pytorch.org/whl/cpu torch && \
    pip install -r requirements.txt

COPY . .

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=180s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:${PORT:-8001}/health')"

# Render injects PORT; fall back to 8001 for local Docker runs.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001} --workers 1"]
