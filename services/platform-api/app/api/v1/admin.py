"""Tenant administration endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.context import get_current_user

router = APIRouter()


class UserUpsert(BaseModel):
    email: str
    full_name: str
    role: str


def _require_admin(user):
    if user.role not in {"admin", "super_admin"}:
        raise HTTPException(403, "Admin role required")


@router.get("/users")
async def list_users(user=Depends(get_current_user)):
    _require_admin(user)
    return {"users": [], "tenant_id": user.tenant_id}


@router.post("/users")
async def create_user(body: UserUpsert, user=Depends(get_current_user)):
    _require_admin(user)
    return {"status": "accepted", "user": body.model_dump(), "tenant_id": user.tenant_id}


@router.patch("/users/{user_id}")
async def update_user(user_id: str, body: UserUpsert, user=Depends(get_current_user)):
    _require_admin(user)
    return {"status": "accepted", "user_id": user_id, "updates": body.model_dump()}


@router.get("/policies")
async def list_policies(user=Depends(get_current_user)):
    _require_admin(user)
    return {"policies": [], "tenant_id": user.tenant_id}


@router.patch("/policies/{policy_id}")
async def update_policy(policy_id: str, user=Depends(get_current_user)):
    _require_admin(user)
    return {"status": "accepted", "policy_id": policy_id}
