"""
Memory Repository - Data access layer for Hindsight Memory.
"""

from __future__ import annotations

from typing import Any, Dict, List
from sqlalchemy import text

try:
    from app.db.session import async_session  # Bridge to platform DB when co-located.
except Exception:  # pragma: no cover - exercised in standalone memory-service tests
    async_session = None


_IN_MEMORY_RECORDS: list[Dict[str, Any]] = []


class MemoryRepository:
    """
    Handles persistence for memory_records.
    Currently bridges to the main platform DB.
    """

    async def save_memory_record(self, record: Dict[str, Any]) -> str:
        if async_session is None:
            _IN_MEMORY_RECORDS.append(record)
            return record["memory_id"]

        try:
            async with async_session() as session:
                # Use the existing memory_records table defined in the schema
                await session.execute(
                    text("""
                    INSERT INTO memory_records 
                    (
                        id, tenant_id, user_id, role, patient_id, memory_type,
                        memory_text_minimized, sensitivity_level, source_workflow_id,
                        content, source, governance_decision, is_active
                    )
                    VALUES (
                        :id, :tenant, :user, :role, :patient, :mtype,
                        :content, :sensitivity, :source_workflow_id,
                        :content, :source, :gov, true
                    )
                    ON CONFLICT (id) DO NOTHING
                    """),
                    {
                        "id": record["memory_id"],
                        "tenant": record["tenant_id"],
                        "user": record["user_id"],
                        "role": record.get("role"),
                        "patient": record.get("patient_id"),
                        "mtype": record["memory_type"],
                        "content": record["memory_text_minimized"],
                        "sensitivity": record.get("sensitivity_level"),
                        "source_workflow_id": record.get("source_workflow_id"),
                        "source": record.get("source_workflow_id", "deep_agent"),
                        "gov": {"decision": "approved", "sensitivity": record.get("sensitivity_level")},
                    },
                )
                await session.commit()
        except Exception:
            _IN_MEMORY_RECORDS.append(record)
        return record["memory_id"]

    async def get_memories_for_user(
        self, tenant_id: str, user_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        if async_session is None:
            scoped = [
                r for r in _IN_MEMORY_RECORDS
                if r.get("tenant_id") == tenant_id and r.get("user_id") == user_id
            ]
            return scoped[-limit:]

        try:
            async with async_session() as session:
                result = await session.execute(
                    text("""
                    SELECT id, memory_type, COALESCE(memory_text_minimized, content) as content, source, created_at
                    FROM memory_records
                    WHERE tenant_id = :tenant AND user_id = :user
                    ORDER BY created_at DESC
                    LIMIT :limit
                    """),
                    {"tenant": tenant_id, "user": user_id, "limit": limit},
                )
                return [dict(r) for r in result.mappings().all()]
        except Exception:
            scoped = [
                r for r in _IN_MEMORY_RECORDS
                if r.get("tenant_id") == tenant_id and r.get("user_id") == user_id
            ]
            return scoped[-limit:]
