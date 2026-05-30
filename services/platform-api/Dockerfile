# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management (optional but recommended)
RUN pip install --no-cache-dir uv

# Copy dependency files first for better caching. This Dockerfile is built from
# the repository root so the platform can import sibling service packages.
COPY services/platform-api/requirements.txt ./requirements.txt

# Install dependencies
RUN uv pip install --system -r requirements.txt 2>/dev/null || pip install -r requirements.txt || pip install \
    fastapi==0.115.* \
    uvicorn[standard]==0.30.* \
    pydantic==2.9.* \
    pydantic-settings==2.5.* \
    sqlalchemy[asyncio]==2.0.* \
    alembic==1.13.* \
    asyncpg==0.29.* \
    redis==5.0.* \
    deepagents==0.5.* \
    langchain==1.2.* \
    langchain-anthropic==1.4.* \
    langchain-core==1.4.* \
    langchain-google-genai==4.2.* \
    langgraph==1.1.* \
    langgraph-checkpoint==3.0.* \
    langgraph-prebuilt==1.0.* \
    langsmith==0.8.* \
    sentence-transformers==3.1.* \
    pgvector==0.2.* \
    python-jose[cryptography]==3.3.* \
    passlib[bcrypt]==1.7.* \
    python-multipart==0.0.12 \
    structlog==24.4.* \
    opentelemetry-api \
    rapidfuzz==3.10.* \
    pypdf==5.0.* \
    python-dotenv==1.0.* \
    httpx==0.28.*

# Copy application code plus sibling service packages used by the platform API.
COPY services/platform-api/ ./
COPY services /workspace/services
ENV PYTHONPATH="/app:/workspace"

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
