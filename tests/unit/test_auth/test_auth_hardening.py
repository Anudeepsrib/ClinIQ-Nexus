import pytest
from fastapi import HTTPException

from app.api.v1.auth import login
from app.core.config import settings, validate_runtime_settings
from app.schemas.auth import LoginRequest


@pytest.mark.asyncio
async def test_demo_login_disabled_when_real_aws_enabled(monkeypatch):
    monkeypatch.setattr(settings, "USE_REAL_AWS", True)
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")

    with pytest.raises(HTTPException) as exc:
        await login(LoginRequest(email="clinician@hospital-a.demo"))

    assert exc.value.status_code == 404


def test_runtime_validation_blocks_wildcard_cors_in_production(monkeypatch):
    monkeypatch.setattr(settings, "USE_REAL_AWS", False)
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "JWT_SECRET", "not-the-dev-secret")
    monkeypatch.setattr(settings, "CORS_ORIGINS", ["*"])

    errors = validate_runtime_settings()

    assert any("CORS_ORIGINS" in error for error in errors)


def test_runtime_validation_requires_cognito_config_in_real_aws(monkeypatch):
    monkeypatch.setattr(settings, "USE_REAL_AWS", True)
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "CORS_ORIGINS", ["https://app.example.com"])
    monkeypatch.setattr(settings, "COGNITO_USER_POOL_ID", "")
    monkeypatch.setattr(settings, "COGNITO_APP_CLIENT_ID", "")

    errors = validate_runtime_settings()

    assert any("COGNITO_USER_POOL_ID" in error for error in errors)
    assert any("COGNITO_APP_CLIENT_ID" in error for error in errors)
