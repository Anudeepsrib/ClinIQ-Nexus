"""
Security, tenant isolation, and governance middleware.

These run on EVERY request and are the primary enforcement points for:
- Authentication (JWT)
- Tenant isolation
- RBAC + ABAC
- Rate limiting
- Correlation IDs for full traceability
"""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Callable, Awaitable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.context import TenantContext, UserContext, set_request_context, clear_request_context, get_current_user
from app.core.security import decode_jwt, create_demo_user_context
from app.core.rate_limit import check_rate_limit

logger = structlog.get_logger(__name__)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Ensures every request has a correlation ID for tracing."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response


class AuthMiddleware(BaseHTTPMiddleware):
    """
    JWT authentication + UserContext construction.
    In production this validates against Cognito JWKS.
    Here we support both real JWTs and demo mode.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Allow public endpoints
        public_paths = {"/health", "/ready", "/", "/docs", "/redoc", "/openapi.json", "/api/v1/auth/login"}
        if request.url.path in public_paths or request.method == "OPTIONS":
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else None

        if not token and settings.ENVIRONMENT == "development" and not settings.USE_REAL_AWS:
            # Demo mode: allow X-Demo-User header for easy testing
            demo_user = request.headers.get("X-Demo-User", "clinician@hospital-a.demo")
            user_ctx = create_demo_user_context(demo_user)
            tenant_ctx = TenantContext(tenant_id=user_ctx.tenant_id)
            set_request_context(tenant_ctx, user_ctx)
            request.state.user = user_ctx
            request.state.tenant = tenant_ctx
            return await call_next(request)

        if not token:
            return JSONResponse(
                status_code=401,
                content={"error": "unauthorized", "message": "Missing Authorization header"},
            )

        try:
            payload = decode_jwt(token)
            
            if settings.USE_REAL_AWS:
                # Map Cognito standard and custom claims
                role = payload.get("custom:role", "patient")
                groups = payload.get("cognito:groups", [])
                if not payload.get("custom:role") and groups:
                    role = groups[0] # Fallback to group if custom:role not set
                
                tenant_id = payload.get("custom:tenant_id", settings.DEFAULT_TENANT_ID)
                assigned_patients_str = payload.get("custom:assigned_patients", "")
                assigned_patients = assigned_patients_str.split(",") if assigned_patients_str else []
                consent_scopes_str = payload.get("custom:consent_scopes", "treatment")
                consent_scopes = [scope.strip() for scope in consent_scopes_str.split(",") if scope.strip()]
                
                user_ctx = UserContext(
                    user_id=payload["sub"],
                    role=role,
                    tenant_id=tenant_id,
                    email=payload.get("email", ""),
                    full_name=payload.get("name", payload.get("given_name", "") + " " + payload.get("family_name", "")).strip(),
                    assigned_patient_ids=set(assigned_patients),
                    can_access_all_patients_in_tenant=role in {"clinician", "care_coordinator"},
                    consent_scopes=consent_scopes or ["treatment"],
                )
            else:
                user_ctx = UserContext(
                    user_id=payload["sub"],
                    role=payload.get("role", "patient"),
                    tenant_id=payload.get("tenant_id", settings.DEFAULT_TENANT_ID),
                    email=payload.get("email", ""),
                    full_name=payload.get("name", ""),
                    assigned_patient_ids=set(payload.get("assigned_patients", [])),
                    can_access_all_patients_in_tenant=payload.get("role") in {"clinician", "care_coordinator"},
                )
                
            tenant_ctx = TenantContext(tenant_id=user_ctx.tenant_id)
            set_request_context(tenant_ctx, user_ctx)
            request.state.user = user_ctx
            request.state.tenant = tenant_ctx
        except Exception as e:
            logger.warning("jwt_validation_failed", error=str(e))
            return JSONResponse(
                status_code=401,
                content={"error": "invalid_token", "message": "Could not validate credentials"},
            )

        try:
            response = await call_next(request)
            return response
        finally:
            clear_request_context()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds browser and transport security headers to every API response."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=(), payment=()",
        )
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-site")

        if request.url.path.startswith("/api/"):
            response.headers.setdefault("Cache-Control", "no-store")

        if settings.USE_REAL_AWS:
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains; preload",
            )

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Distributed rate limiting using Redis."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if not hasattr(request.state, "user"):
            return await call_next(request)

        user: UserContext = request.state.user
        limit = settings.RATE_LIMIT_DEFAULT

        if user.role == "patient":
            limit = settings.RATE_LIMIT_PATIENT
        elif user.role in {"clinician", "nurse"}:
            limit = settings.RATE_LIMIT_CLINICIAN
        elif "agent" in request.url.path or "workflow" in request.url.path:
            limit = settings.RATE_LIMIT_AGENTIC

        try:
            allowed, remaining, reset = await check_rate_limit(
                key=f"rate:{user.tenant_id}:{user.user_id}",
                limit=limit,
                window=60,
            )
        except Exception as exc:
            logger.error(
                "rate_limit_backend_unavailable",
                tenant_id=user.tenant_id,
                user_id=user.user_id,
                role=user.role,
                error=str(exc),
            )
            if settings.USE_REAL_AWS:
                return JSONResponse(
                    status_code=503,
                    content={
                        "error": "rate_limit_unavailable",
                        "message": "Request governance is temporarily unavailable.",
                    },
                )

            response = await call_next(request)
            response.headers["X-RateLimit-Policy"] = "degraded-dev-open"
            return response

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limited",
                    "message": "Too many requests. Please slow down.",
                    "retry_after": reset,
                },
                headers={"Retry-After": str(reset), "X-RateLimit-Remaining": "0"},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Enforce maximum request body size to prevent DoS / resource exhaustion."""

    def __init__(self, app: Callable, max_bytes: int | None = None) -> None:
        super().__init__(app)
        if max_bytes is None:
            from app.core.config import settings as _s
            max_bytes = _s.MAX_REQUEST_BYTES
        self.max_bytes = max_bytes

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_bytes:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": "payload_too_large",
                            "message": f"Request body exceeds limit of {self.max_bytes} bytes",
                            "max_bytes": self.max_bytes,
                        },
                    )
            except ValueError:
                pass  # Invalid header; let downstream handle
        # Note: for chunked without length we rely on uvicorn/server limits too
        return await call_next(request)


class RequestTimeoutMiddleware(BaseHTTPMiddleware):
    """Hard timeout per request to avoid hanging workers (enterprise reliability)."""

    def __init__(self, app: Callable, timeout_seconds: float | None = None) -> None:
        super().__init__(app)
        if timeout_seconds is None:
            from app.core.config import settings as _s
            timeout_seconds = _s.REQUEST_TIMEOUT_SECONDS
        self.timeout_seconds = timeout_seconds

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        correlation_id = getattr(request.state, "correlation_id", None)
        try:
            return await asyncio.wait_for(call_next(request), timeout=self.timeout_seconds)
        except asyncio.TimeoutError:
            logger.warning(
                "request_timeout",
                path=request.url.path,
                method=request.method,
                correlation_id=correlation_id,
                timeout=self.timeout_seconds,
            )
            return JSONResponse(
                status_code=504,
                content={
                    "error": "gateway_timeout",
                    "message": "Request timed out. Please retry.",
                    "correlation_id": correlation_id,
                },
            )


class TenantIsolationMiddleware(BaseHTTPMiddleware):
    """
    Hard enforcement that tenant_id from token matches resource access.
    This is the foundation of multi-tenant isolation.
    Enhanced: inspects common path patterns for patient/tenant resources and enforces ABAC early.
    """

    # Paths that carry patient_id in path and should be validated
    PATIENT_PATH_PATTERNS = ("/patients/", "/documents/", "/memory/", "/reviews/", "/workflows/")

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # If context populated (Auth ran before us), perform early tenant + ABAC guard for sensitive paths.
        # This provides belt-and-suspenders defense; endpoint Depends remain authoritative.
        if hasattr(request.state, "user") and hasattr(request.state, "tenant"):
            try:
                user: UserContext = request.state.user
                tenant: TenantContext = request.state.tenant
                path = request.url.path
                # Basic tenant match (future: parse path params for explicit tenant)
                # For patient-scoped: rely on can_access_patient which is called in routers.
                # Here we can reject obvious cross-tenant attempts if query params expose tenant_id mismatch.
                q_tenant = request.query_params.get("tenant_id")
                if q_tenant and q_tenant != tenant.tenant_id:
                    logger.warning("tenant_isolation_violation", path=path, claimed=q_tenant, actual=tenant.tenant_id)
                    return JSONResponse(
                        status_code=403,
                        content={"error": "tenant_isolation", "message": "Tenant mismatch in request"},
                    )
                # Patient ABAC pre-filter for paths known to be patient specific
                if any(p in path for p in self.PATIENT_PATH_PATTERNS):
                    pid = None
                    # naive extract last path segment if looks like patient id
                    parts = [p for p in path.split("/") if p]
                    if len(parts) >= 2 and parts[-2] in {"patients", "patient"}:
                        pid = parts[-1]
                    if pid and not user.can_access_patient(pid) and not user.is_admin_role:
                        logger.warning("patient_abac_block", user_id=user.user_id, patient_id=pid, path=path)
                        return JSONResponse(
                            status_code=403,
                            content={"error": "forbidden", "message": "Insufficient access to patient resource"},
                        )
            except Exception as exc:
                logger.debug("tenant_mw_check_skipped", error=str(exc))

        response = await call_next(request)
        return response
