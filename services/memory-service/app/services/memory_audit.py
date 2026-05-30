"""
Memory Audit - Records every memory decision for compliance.
"""

from __future__ import annotations

from datetime import datetime
import uuid

MEMORY_AUDIT_EVENTS: list[dict] = []


class MemoryAuditService:
    """
    Creates immutable audit records for all memory operations.
    """

    async def log_memory_decision(
        self,
        tenant_id: str,
        user_id: str,
        decision: str,  # approved | blocked | retrieved
        candidate_content: str | None,
        minimized_content: str | None,
        reason: str,
        policy_tags: list[str],
    ) -> str:
        audit_id = f"mem_audit_{uuid.uuid4().hex[:12]}"

        MEMORY_AUDIT_EVENTS.append({
            "audit_id": audit_id,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "decision": decision,
            "candidate_content": candidate_content,
            "minimized_content": minimized_content,
            "reason": reason,
            "policy_tags": policy_tags,
            "created_at": datetime.utcnow().isoformat(),
        })

        return audit_id

    async def get_memory_audit(self, audit_or_memory_id: str) -> list[dict]:
        return [
            event for event in MEMORY_AUDIT_EVENTS
            if event["audit_id"] == audit_or_memory_id or audit_or_memory_id in str(event)
        ]
