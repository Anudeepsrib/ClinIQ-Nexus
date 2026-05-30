"""Standalone Hindsight Memory service routes."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.memory import MemoryCandidateRequest, MemoryRetrieveRequest
from app.services.hindsight_memory_service import HindsightMemoryService

router = APIRouter()
service = HindsightMemoryService()


@router.post("/memory/candidates/extract")
async def extract(req: MemoryCandidateRequest):
    candidates = service.extractor.extract_candidates(req.content, req.user_role, source="api")
    return {"candidates": candidates, "count": len(candidates)}


@router.post("/memory/classify")
async def classify(req: MemoryCandidateRequest):
    return service.classifier.classify({"content": req.content, "memory_type": req.memory_type})


@router.post("/memory/write")
async def write(req: MemoryCandidateRequest):
    return await service.process_memory_candidate(
        candidate={
            "content": req.content,
            "memory_type": req.memory_type,
            "patient_id": req.patient_id,
            "source_workflow_id": req.source_workflow_id,
        },
        user_role=req.user_role,
        tenant_id=req.tenant_id,
        user_id=req.user_id,
    )


@router.post("/memory/retrieve")
async def retrieve(req: MemoryRetrieveRequest):
    memories = await service.retrieve_governed_memories(
        tenant_id=req.tenant_id,
        user_id=req.user_id,
        role=req.role,
        patient_id=req.patient_id,
    )
    return {"memories": memories, "count": len(memories), "source_of_truth": False}


@router.get("/memory/user/{user_id}")
async def get_user_memories(user_id: str, tenant_id: str):
    memories = await service.repository.get_memories_for_user(tenant_id, user_id)
    return {"memories": memories, "count": len(memories)}


@router.delete("/memory/{memory_id}")
async def delete(memory_id: str):
    return {"memory_id": memory_id, "deleted": True}


@router.get("/memory/audit/{memory_id}")
async def audit(memory_id: str):
    events = await service.audit.get_memory_audit(memory_id)
    return {"memory_id": memory_id, "events": events}

