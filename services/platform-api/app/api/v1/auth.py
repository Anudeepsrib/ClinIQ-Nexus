"""Authentication endpoints (demo + real Cognito path)."""

from fastapi import APIRouter, Depends, HTTPException

from app.core.config import settings
from app.core.security import create_demo_token, create_demo_user_context
from app.core.context import get_current_user
from app.schemas.auth import LoginRequest, TokenResponse, UserMe

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    """Demo login. In production this would exchange Cognito code or SRP."""
    if settings.USE_REAL_AWS or settings.ENVIRONMENT != "development":
        raise HTTPException(
            status_code=404,
            detail="Local demo login is disabled outside development. Use Cognito authentication.",
        )

    if "@" not in body.email:
        raise HTTPException(400, "Invalid email format")

    token = create_demo_token(body.email)
    user = create_demo_user_context(body.email)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=28800,
        user={
            "id": user.user_id,
            "email": user.email,
            "role": user.role,
            "name": user.full_name,
            "tenant_id": user.tenant_id,
        },
    )


@router.get("/me", response_model=UserMe)
async def get_me(user=Depends(get_current_user)):
    return UserMe(
        id=user.user_id,
        email=user.email,
        role=user.role,
        name=user.full_name,
        tenant_id=user.tenant_id,
        assigned_patients=list(user.assigned_patient_ids),
    )


@router.post("/logout")
async def logout(user=Depends(get_current_user)):
    return {"status": "logged_out", "user_id": user.user_id}
