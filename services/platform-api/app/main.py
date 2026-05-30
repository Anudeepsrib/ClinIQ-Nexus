"""
ClinIQ-Nexus Platform API
Enterprise-grade, HIPAA-aware clinical AI platform for hospitals.

This is the primary service demonstrating all architectural patterns:
- Deterministic-first Intent Routing
- Mandatory MCP Context Governance
- RBAC + ABAC + Tenant Isolation
- Full audit trail
- LangGraph agent workflows with Human-in-the-Loop
- Safe RAG with pgvector (local) / OpenSearch (prod)
"""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.context import TenantContext, UserContext, set_request_context
from app.core.exceptions import ClinIQException, handle_cliniq_exception
from app.core.logging import configure_logging
from app.core.middleware import (
    CorrelationIdMiddleware,
    RateLimitMiddleware,
    TenantIsolationMiddleware,
    AuthMiddleware,
)
from app.api.v1 import router as api_v1_router
from app.models.base import Base
from app.db.session import engine, get_db

# Configure structured logging
configure_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    logger.info("starting_cliniq_nexus", environment=settings.ENVIRONMENT)

    # Local dev convenience: migrations + seed are run via docker-compose command
    # In real production these are separate jobs
    if settings.ENVIRONMENT == "development":
        logger.info("local_dev_mode_active")

    yield

    logger.info("shutting_down_cliniq_nexus")
    await engine.dispose()


app = FastAPI(
    title="ClinIQ-Nexus Platform API",
    description=(
        "HIPAA-compliant, multi-tenant clinical AI platform. "
        "Never diagnoses, prescribes, or makes final clinical decisions. "
        "All outputs for safety-sensitive workflows require human review."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Security headers + CORS (locked down for demo; tighten in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=600,
)

# Core middleware stack (order matters)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(TenantIsolationMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(RateLimitMiddleware)


@app.exception_handler(ClinIQException)
async def cliniq_exception_handler(request: Request, exc: ClinIQException) -> JSONResponse:
    return handle_cliniq_exception(request, exc)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Never leak stack traces to clients."""
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    logger.error(
        "unhandled_exception",
        correlation_id=correlation_id,
        path=request.url.path,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred. Please contact support.",
            "correlation_id": correlation_id,
        },
    )


# Mount API
app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/health", tags=["System"])
async def health_check() -> dict:
    """Liveness / readiness probe."""
    return {
        "status": "healthy",
        "service": "platform-api",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT,
        "use_real_aws": settings.USE_REAL_AWS,
    }


@app.get("/ready", tags=["System"])
async def readiness_check() -> dict:
    """Readiness probe (checks critical dependencies)."""
    from app.db.session import async_session
    
    db_ok = False
    redis_ok = False
    
    try:
        async with async_session() as session:
            await session.execute("SELECT 1")
            db_ok = True
    except Exception:
        logger.exception("readiness_db_check_failed")
    
    try:
        from app.core.cache import get_redis
        redis = await get_redis()
        await redis.ping()
        redis_ok = True
    except Exception:
        logger.exception("readiness_redis_check_failed")
    
    status = "ready" if (db_ok and redis_ok) else "degraded"
    
    return {
        "status": status,
        "database": "ok" if db_ok else "unavailable",
        "redis": "ok" if redis_ok else "unavailable",
        "vector_store": "pgvector (local)" if not settings.USE_REAL_AWS else "opensearch",
    }


# Root info (useful for demos)
@app.get("/", include_in_schema=False)
async def root() -> dict:
    return {
        "name": "ClinIQ-Nexus",
        "tagline": "Safe, governed clinical AI for hospitals",
        "docs": "/docs",
        "health": "/health",
        "note": "This is a reference implementation. All clinical outputs require human review.",
    }
