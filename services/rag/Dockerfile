FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PYTHONUNBUFFERED=1
ENV CHROMA_HOST=chromadb
ENV CHROMA_PORT=8000
ENV COLLECTION_NAME=ops_knowledge

# Copy dependencies definitions
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
COPY README.md ./
RUN uv sync --frozen --no-dev

# Pre-download and cache default ONNX embedding model inside image for offline runtime
RUN uv run python -c "from chromadb.utils import embedding_functions; ef = embedding_functions.DefaultEmbeddingFunction(); ef(['pre-warm cache'])" || true

EXPOSE 8000

CMD ["uv", "run", "rag"]
