"""Governed Hindsight Memory APIs."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.context import get_current_user
from app.services.memory.service import memory_service

router = APIRouter()


class MemoryTextRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)
    memory_type: str = "preference"
    patient_id: Optional[str] = None
    source_workflow_id: Optional[str] = None


class MemoryRetrieveRequest(BaseModel):
    patient_id: Optional[str] = None
    query: Optional[str] = None


def _full_service():
    service = getattr(memory_service, "_service", None)
    if service is None:
        raise HTTPException(503, "Hindsight Memory service is unavailable")
    return service


@router.post("/candidates/extract")
async def extract_candidates(req: MemoryTextRequest, user=Depends(get_current_user)):
    service = _full_service()
    candidates = service.extractor.extract_candidates(req.content, user.role, source="api")
    return {"candidates": candidates, "count": len(candidates)}


@router.post("/classify")
async def classify(req: MemoryTextRequest, user=Depends(get_current_user)):
    service = _full_service()
    candidate = {"content": req.content, "memory_type": req.memory_type, "patient_id": req.patient_id}
    return service.classifier.classify(candidate)


@router.post("/write")
async def write(req: MemoryTextRequest, user=Depends(get_current_user)):
    service = _full_service()
    return await service.process_memory_candidate(
        candidate={
            "content": req.content,
            "memory_type": req.memory_type,
            "patient_id": req.patient_id,
            "source_workflow_id": req.source_workflow_id,
        },
        user_role=user.role,
        tenant_id=user.tenant_id,
        user_id=user.user_id,
    )


@router.post("/retrieve")
async def retrieve(req: MemoryRetrieveRequest, user=Depends(get_current_user)):
    memories = await memory_service.retrieve_relevant(user=user, patient_id=req.patient_id)
    return {"memories": memories, "count": len(memories), "source_of_truth": False}


@router.get("/user/{user_id}")
async def get_user_memories(user_id: str, user=Depends(get_current_user)):
    if user_id != user.user_id and user.role not in {"admin", "compliance_officer"}:
        raise HTTPException(403, "Cannot access another user's memories")
    service = _full_service()
    records = await service.repository.get_memories_for_user(user.tenant_id, user_id)
    return {"memories": records, "count": len(records)}


@router.delete("/{memory_id}")
async def delete_memory(memory_id: str, user=Depends(get_current_user)):
    service = _full_service()
    records = await service.repository.get_memories_for_user(user.tenant_id, user.user_id, limit=1000)
    deleted = False
    for record in records:
        if record.get("memory_id") == memory_id or record.get("id") == memory_id:
            record["is_active"] = False
            deleted = True
    return {"memory_id": memory_id, "deleted": deleted}


@router.get("/audit/{memory_id}")
async def get_memory_audit(memory_id: str, user=Depends(get_current_user)):
    service = _full_service()
    events = await service.audit.get_memory_audit(memory_id)
    return {"memory_id": memory_id, "events": events}
