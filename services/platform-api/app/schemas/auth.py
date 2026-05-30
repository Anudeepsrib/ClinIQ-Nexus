"""Pydantic schemas for auth."""

from pydantic import BaseModel, EmailStr
from typing import List, Optional


class LoginRequest(BaseModel):
    email: EmailStr
    password: Optional[str] = None  # ignored in demo


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class UserMe(BaseModel):
    id: str
    email: str
    role: str
    name: str
    tenant_id: str
    assigned_patients: List[str] = []
