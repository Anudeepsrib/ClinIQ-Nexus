"""Application configuration (Pydantic Settings v2)."""

from __future__ import annotations

from typing import List

from pydantic import Field
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
    DATABASE_URL: str = "postgresql+asyncpg://cliniq:cliniq_dev_password@localhost:5432/cliniq_nexus"
    OPENSEARCH_URL: str = "https://search-cliniq-nexus-dev-xxxxx.us-east-1.es.amazonaws.com"
    S3_BUCKET_NAME: str = "cliniq-nexus-dev-documents"

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


    # CORS (tighten in production)
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Tenant (used heavily in demo)
    DEFAULT_TENANT_ID: str = "tenant_hospital_a"

    # Rate limiting
    RATE_LIMIT_DEFAULT: int = 60  # requests per minute
    RATE_LIMIT_PATIENT: int = 20
    RATE_LIMIT_CLINICIAN: int = 80
    RATE_LIMIT_AGENTIC: int = 10  # stricter for heavy workflows

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


settings = Settings()


def validate_runtime_settings() -> list[str]:
    """Return blocking configuration errors for non-development runtimes."""
    errors: list[str] = []
    production_like = settings.USE_REAL_AWS or settings.ENVIRONMENT in {"stage", "staging", "prod", "production"}

    if not production_like:
        return errors

    if "*" in settings.CORS_ORIGINS:
        errors.append("CORS_ORIGINS must not contain '*' in production-like environments")

    if settings.USE_REAL_AWS:
        if not settings.COGNITO_USER_POOL_ID:
            errors.append("COGNITO_USER_POOL_ID is required when USE_REAL_AWS=true")
        if not settings.COGNITO_APP_CLIENT_ID:
            errors.append("COGNITO_APP_CLIENT_ID is required when USE_REAL_AWS=true")

    if not settings.USE_REAL_AWS and settings.JWT_SECRET == "dev-jwt-secret-change-in-prod-please":
        errors.append("JWT_SECRET must be changed outside local development")

    return errors
