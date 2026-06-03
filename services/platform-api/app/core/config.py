"""Application configuration (Pydantic Settings v2).
Enterprise: supports *_FILE for docker/k8s secrets (no env var leak in ps).
"""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Core
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    USE_REAL_AWS: bool = False

    # Database & Storage
    DATABASE_URL: str = "postgresql+asyncpg://careos:careos_dev_password@localhost:5432/careos"
    OPENSEARCH_URL: str = "https://search-careos-dev-xxxxx.us-east-1.es.amazonaws.com"
    S3_BUCKET_NAME: str = "careos-dev-documents"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Auth (local mock mode or AWS Cognito)
    JWT_SECRET: str = "dev-jwt-secret-change-in-prod-please"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 8  # 8 hours
    
    # AWS Cognito
    AWS_REGION: str = "us-east-1"
    COGNITO_USER_POOL_ID: str = ""
    COGNITO_APP_CLIENT_ID: str = ""

    # Secret file support (enterprise docker/k8s pattern)
    JWT_SECRET_FILE: str | None = None
    DATABASE_URL_FILE: str | None = None


    # CORS (tighten in production)
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Tenant (used heavily in demo)
    DEFAULT_TENANT_ID: str = "tenant_hospital_a"

    # Rate limiting
    RATE_LIMIT_DEFAULT: int = 60  # requests per minute
    RATE_LIMIT_PATIENT: int = 20
    RATE_LIMIT_CLINICIAN: int = 80
    RATE_LIMIT_AGENTIC: int = 10  # stricter for heavy workflows

    # Hardening / reliability
    MAX_REQUEST_BYTES: int = 10 * 1024 * 1024  # 10 MiB
    REQUEST_TIMEOUT_SECONDS: float = 45.0

    # DB pool (tune per workload; larger in prod)
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Safety / MCP
    MCP_MIN_CONFIDENCE_FOR_AUTO: float = 0.75
    REQUIRE_HUMAN_REVIEW_CONFIDENCE_BELOW: float = 0.65
    SAFETY_LEXICON_ENABLED: bool = True

    # Model routing (mock by default)
    MODEL_ROUTER_DEFAULT: str = "mock-bedrock-claude-3.5-sonnet"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Feature flags
    ENABLE_MEMORY_SERVICE: bool = True
    ENABLE_DEEP_AGENT_PATTERNS: bool = True

    @model_validator(mode="after")
    def _apply_secret_files_and_defaults(self) -> "Settings":
        # Support Docker/K8s secret files
        if self.JWT_SECRET_FILE:
            content = _read_secret_file(self.JWT_SECRET_FILE)
            if content:
                self.JWT_SECRET = content
        if self.DATABASE_URL_FILE:
            content = _read_secret_file(self.DATABASE_URL_FILE)
            if content:
                self.DATABASE_URL = content
        return self


def _read_secret_file(path: str | None) -> str | None:
    if not path:
        return None
    try:
        p = Path(path)
        if p.exists():
            return p.read_text(encoding="utf-8").strip()
    except Exception:
        pass
    return None


# Post-init secret file support (e.g. JWT_SECRET_FILE=/run/secrets/jwt_secret)
def apply_secret_files(s: "Settings") -> "Settings":
    for secret_field, file_field in [
        ("JWT_SECRET", "JWT_SECRET_FILE"),
        ("DATABASE_URL", "DATABASE_URL_FILE"),
    ]:
        file_val = getattr(s, file_field, None) or os.environ.get(file_field)
        content = _read_secret_file(file_val)
        if content:
            setattr(s, secret_field, content)
    return s


settings = Settings()
# Apply any remaining secret files from env (for cases where field not populated yet)
apply_secret_files(settings)


def validate_runtime_settings() -> list[str]:
    """Return blocking configuration errors for non-development runtimes."""
    errors: list[str] = []
    production_like = settings.USE_REAL_AWS or settings.ENVIRONMENT in {"stage", "staging", "prod", "production"}

    if not production_like:
        # Still block the known dev secret in any non-dev env
        if settings.ENVIRONMENT not in {"development", "dev", "local"} and settings.JWT_SECRET == "dev-jwt-secret-change-in-prod-please":
            errors.append("JWT_SECRET must be changed for non-development environments")
        return errors

    if "*" in settings.CORS_ORIGINS:
        errors.append("CORS_ORIGINS must not contain '*' in production-like environments")

    if settings.USE_REAL_AWS:
        if not settings.COGNITO_USER_POOL_ID:
            errors.append("COGNITO_USER_POOL_ID is required when USE_REAL_AWS=true")
        if not settings.COGNITO_APP_CLIENT_ID:
            errors.append("COGNITO_APP_CLIENT_ID is required when USE_REAL_AWS=true")

    if settings.JWT_SECRET == "dev-jwt-secret-change-in-prod-please":
        errors.append("JWT_SECRET must be changed in production-like runs (use secret file or strong random)")

    if len(settings.JWT_SECRET) < 32:
        errors.append("JWT_SECRET must be at least 32 characters for production-like security")

    # Database URL should not contain obvious dev passwords in prod-like
    if "careos_dev_password" in (settings.DATABASE_URL or "") and production_like:
        errors.append("DATABASE_URL must not contain development passwords in production-like environments")

    return errors
