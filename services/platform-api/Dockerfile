# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

# Enterprise hardening labels
LABEL org.opencontainers.image.title="ClinIQ-Nexus Platform API" \
      org.opencontainers.image.description="Enterprise hardened, HIPAA-aware clinical AI platform API" \
      org.opencontainers.image.source="https://github.com/example/ClinIQ-Nexus" \
      security.non-root="true"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONFAULTHANDLER=1

WORKDIR /app

# System dependencies (minimal; libpq-dev only needed for build of asyncpg/psycopg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user early (principle of least privilege)
RUN groupadd -r appgroup --gid 1001 && \
    useradd -r -g appgroup --uid 1001 --home /app --shell /sbin/nologin appuser && \
    mkdir -p /app /workspace && \
    chown -R appuser:appgroup /app /workspace

# Install uv for fast dependency management (optional but recommended)
RUN pip install --no-cache-dir uv

# Copy dependency files first for better caching. This Dockerfile is built from
# the repository root so the platform can import sibling service packages.
COPY --chown=appuser:appgroup services/platform-api/requirements.txt ./requirements.txt

# Install dependencies as root then drop (some native wheels need it)
RUN uv pip install --system -r requirements.txt 2>/dev/null || pip install --no-cache-dir -r requirements.txt || pip install --no-cache-dir \
    fastapi==0.115.0 \
    uvicorn[standard]==0.30.6 \
    pydantic[email]==2.9.2 \
    pydantic-settings==2.5.2 \
    sqlalchemy[asyncio]==2.0.35 \
    alembic==1.13.3 \
    asyncpg==0.29.0 \
    redis==5.0.8 \
    deepagents==0.5.0 \
    langchain==1.2.18 \
    langchain-anthropic==1.4.4 \
    langchain-core==1.4.0 \
    langchain-google-genai==4.2.4 \
    langgraph==1.1.10 \
    langgraph-checkpoint==3.0.1 \
    langgraph-prebuilt==1.0.13 \
    langsmith==0.8.7 \
    sentence-transformers==3.1.1 \
    pgvector==0.3.2 \
    python-jose[cryptography]==3.3.0 \
    passlib[bcrypt]==1.7.4 \
    python-multipart==0.0.12 \
    structlog==24.4.0 \
    opentelemetry-api==1.24.0 \
    rapidfuzz==3.10.1 \
    pypdf==5.0.1 \
    python-dotenv==1.0.1 \
    httpx==0.28.1

# Copy application code plus sibling service packages used by the platform API.
COPY --chown=appuser:appgroup services/platform-api/ ./
COPY --chown=appuser:appgroup services /workspace/services
ENV PYTHONPATH="/app:/workspace"

# Drop to non-root
USER appuser

EXPOSE 8000

# Use /ready for better readiness signal in k8s/ecs
HEALTHCHECK --interval=30s --timeout=8s --start-period=10s --retries=3 \
    CMD curl -f --max-time 5 http://127.0.0.1:8000/ready || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
