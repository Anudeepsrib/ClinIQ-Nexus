"""
Memory Writer - Handles the final write of approved memories.
"""

from __future__ import annotations

from typing import Any, Dict
from datetime import datetime
import uuid


class MemoryWriter:
    """
    Persists approved memories after governance has passed.
    """

    async def write_approved_memory(
        self,
        tenant_id: str,
        user_id: str,
        role: str,
        minimized_content: str,
        memory_type: str,
        sensitivity_level: str,
        source_workflow_id: str | None = None,
        patient_id: str | None = None,
    ) -> Dict[str, Any]:
        """
        Write a memory that has already passed governance.
        Returns the created memory record.
        """
        memory_id = f"mem_{uuid.uuid4().hex[:12]}"

        # In real implementation this would INSERT into memory_records table
        # using the repository and also create a memory_policy_decision record.

        record = {
            "memory_id": memory_id,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "role": role,
            "patient_id": patient_id,
            "memory_type": memory_type,
            "memory_text_minimized": minimized_content,
            "sensitivity_level": sensitivity_level,
            "source_workflow_id": source_workflow_id,
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True,
        }

        return record
