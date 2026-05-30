"""
Memory Retriever - Handles governed retrieval of Hindsight Memory.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..repositories.memory_repository import MemoryRepository


FORBIDDEN_CLINICAL_TERMS = {
    "diagnosis",
    "diagnosed",
    "lab",
    "troponin",
    "potassium",
    "creatinine",
    "glucose",
    "sodium",
    "medication",
    "dose",
    "psychotherapy",
    "atrial fibrillation",
    "treatment",
}


class MemoryRetriever:
    """
    Retrieves approved, minimized memories with proper scoping.
    """

    def __init__(self, repository: Optional[MemoryRepository] = None):
        self.repository = repository or MemoryRepository()

    async def retrieve_for_context(
        self,
        tenant_id: str,
        user_id: str,
        role: str,
        patient_id: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve memories that are safe for this exact context.
        Memory is secondary context only. It is never used as clinical truth.
        """
        records = await self.repository.get_memories_for_user(
            tenant_id=tenant_id,
            user_id=user_id,
            limit=max(limit * 2, limit),
        )

        approved: List[Dict[str, Any]] = []
        for record in records:
            if record.get("tenant_id") and record["tenant_id"] != tenant_id:
                continue
            if record.get("user_id") and record["user_id"] != user_id:
                continue
            if record.get("role") and record["role"] != role:
                continue
            if patient_id and record.get("patient_id") not in {None, patient_id}:
                continue

            text = record.get("memory_text_minimized") or record.get("content") or ""
            lowered = text.lower()
            if not text or any(term in lowered for term in FORBIDDEN_CLINICAL_TERMS):
                continue

            sensitivity = record.get("sensitivity_level") or "low"
            if sensitivity not in {"low", "medium"}:
                continue

            approved.append({
                "memory_id": record.get("memory_id") or record.get("id"),
                "memory_type": record.get("memory_type"),
                "memory_text_minimized": text,
                "sensitivity_level": sensitivity,
                "source_workflow_id": record.get("source_workflow_id"),
                "patient_id": record.get("patient_id"),
            })
            if len(approved) >= limit:
                break

        return approved
