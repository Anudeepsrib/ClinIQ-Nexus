"""Memory service configuration."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class MemorySettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENVIRONMENT: str = "development"
    MEMORY_RETENTION_DAYS: int = 365
    ALLOW_PATIENT_SCOPED_MEMORY: bool = True


settings = MemorySettings()

