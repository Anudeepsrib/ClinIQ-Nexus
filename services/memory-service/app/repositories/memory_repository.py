"""
Memory Repository - Data access layer for Hindsight Memory.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from sqlalchemy import text

from app.db.session import async_session  # Bridge to platform DB for now


class MemoryRepository:
    """
    Handles persistence for memory_records.
    Currently bridges to the main platform DB.
    """

    async def save_memory_record(self, record: Dict[str, Any]) -> str:
        async with async_session() as session:
            # Use the existing memory_records table defined in the schema
            await session.execute(
                text("""
                    INSERT INTO memory_records 
                    (id, tenant_id, user_id, patient_id, memory_type, content, source, governance_decision)
                    VALUES (:id, :tenant, :user, :patient, :mtype, :content, :source, :gov)
                    ON CONFLICT (id) DO NOTHING
                """),
                {
                    "id": record["memory_id"],
                    "tenant": record["tenant_id"],
                    "user": record["user_id"],
                    "patient": record.get("patient_id"),
                    "mtype": record["memory_type"],
                    "content": record["memory_text_minimized"],
                    "source": record.get("source_workflow_id", "deep_agent"),
                    "gov": {"decision": "approved", "sensitivity": record.get("sensitivity_level")},
                },
            )
            await session.commit()
        return record["memory_id"]

    async def get_memories_for_user(
        self, tenant_id: str, user_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        async with async_session() as session:
            result = await session.execute(
                text("""
                    SELECT id, memory_type, content, source, created_at
                    FROM memory_records
                    WHERE tenant_id = :tenant AND user_id = :user
                    ORDER BY created_at DESC
                    LIMIT :limit
                """),
                {"tenant": tenant_id, "user": user_id, "limit": limit},
            )
            return [dict(r) for r in result.mappings().all()]
