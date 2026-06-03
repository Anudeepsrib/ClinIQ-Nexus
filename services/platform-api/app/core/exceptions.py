"""Domain exceptions with safe client responses."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import Request
from fastapi.responses import JSONResponse


class CareOSException(Exception):
    """Base exception for all controlled errors."""
    status_code: int = 400
    error_code: str = "bad_request"

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class UnauthorizedError(CareOSException):
    status_code = 401
    error_code = "unauthorized"


class ForbiddenError(CareOSException):
    status_code = 403
    error_code = "forbidden"


class NotFoundError(CareOSException):
    status_code = 404
    error_code = "not_found"


class RateLimitExceeded(CareOSException):
    status_code = 429
    error_code = "rate_limited"


class SafetyViolationError(CareOSException):
    """Raised when a clinical safety rule is violated."""
    status_code = 422
    error_code = "safety_violation"


class MCPBlockedError(CareOSException):
    """Context governance blocked the request."""
    status_code = 422
    error_code = "mcp_blocked"


def handle_careos_exception(request: Request, exc: CareOSException) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "correlation_id": correlation_id,
        },
    )
