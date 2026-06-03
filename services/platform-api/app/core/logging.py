"""Structured logging configuration (structlog).
Enterprise hardening: PHI/PII redaction is non-optional for healthcare workloads.
"""

from __future__ import annotations

import logging
import re
import sys
from typing import Any

import structlog

# Sensitive keys whose values should be redacted (case-insensitive match on key)
SENSITIVE_KEYS = {
    "password", "passwd", "secret", "token", "api_key", "apikey",
    "ssn", "social_security", "dob", "date_of_birth", "mrn", "medical_record",
    "phi", "patient_name", "full_name", "name",  # name is broad; we redact in clinical contexts only via event
    "address", "phone", "email",  # emails often ok for audit but redact in some flows
    "consent_detail", "raw_content", "document_text", "chunk_text",
}

# Regex patterns for common PII/PHI in free-text values (conservative)
_PII_PATTERNS = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED-SSN]"),
    (re.compile(r"\b\d{2}/\d{2}/\d{4}\b"), "[REDACTED-DOB]"),
    (re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"), "[REDACTED-PHONE]"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "[REDACTED-EMAIL]"),  # broad
    (re.compile(r"\b(MRN|mrn)[:\s-]*[A-Za-z0-9-]{4,}\b"), "[REDACTED-MRN]"),
]

def _redact_value(value: Any, key: str | None = None) -> Any:
    """Recursively redact sensitive values."""
    if isinstance(value, dict):
        return {k: _redact_value(v, k) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return type(value)(_redact_value(v) for v in value)
    if isinstance(value, str):
        # Key-based redaction
        if key and key.lower().replace("-", "_").replace(" ", "_") in SENSITIVE_KEYS:
            return "[REDACTED]"
        # Pattern redaction for free text (e.g. audit messages containing chunks)
        redacted = value
        for pattern, repl in _PII_PATTERNS:
            redacted = pattern.sub(repl, redacted)
        # Never let very long free text (e.g. full notes) through in logs
        if len(redacted) > 512:
            redacted = redacted[:509] + "...[TRUNC]"
        return redacted
    return value


def redact_sensitive_processor(logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """structlog processor: removes or masks PHI/PII before rendering."""
    # Always redact known event keys that carry clinical content
    for k in list(event_dict.keys()):
        lk = k.lower().replace("-", "_")
        if lk in SENSITIVE_KEYS or "content" in lk or "text" in lk or "chunk" in lk or "note" in lk:
            event_dict[k] = _redact_value(event_dict[k], k)
        else:
            event_dict[k] = _redact_value(event_dict[k], k)
    return event_dict


def configure_logging() -> None:
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        redact_sensitive_processor,  # PHI redaction MUST run before timestamp/renderer
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer() if sys.stderr.isatty() else structlog.processors.JSONRenderer(),
    ]

    structlog.configure(
        processors=processors,
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Quiet noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    # Never log at DEBUG level for sqlalchemy in prod (could leak queries with PHI)
    if logging.getLogger().level <= logging.DEBUG:
        logging.getLogger("sqlalchemy").setLevel(logging.INFO)
