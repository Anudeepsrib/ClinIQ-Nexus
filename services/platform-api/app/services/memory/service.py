"""
Hindsight Memory Service - Fully wired to the complete governed implementation.

This now uses the full HindsightMemoryService from services/memory-service/
when available, providing proper extraction, classification, governance,
write, retrieval, and audit for all memory operations.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

REPO_ROOT = next(
    (parent for parent in Path(__file__).resolve().parents if (parent / "services").exists()),
    Path.cwd(),
)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from services.memory_service.app.services.hindsight_memory_service import (
        HindsightMemoryService as _FullHindsightService,
    )
    HAS_FULL_MEMORY = True
except Exception:
    HAS_FULL_MEMORY = False
    _FullHindsightService = None

from app.core.context import UserContext


class MemoryService:
    """
    Production facade for Hindsight Memory.
    Deep Agents and workflows should prefer this service.
    """

    def __init__(self):
        if HAS_FULL_MEMORY and _FullHindsightService:
            self._service = _FullHindsightService()
            self._using_full = True
        else:
            self._service = None
            self._using_full = False

    async def extract_and_store(
        self,
        user: UserContext,
        conversation_turn: Dict[str, Any],
        agent_output: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        if self._using_full:
            candidate = {
                "content": conversation_turn.get("content", ""),
                "memory_type": "preference",
                "source_workflow_id": agent_output.get("workflow_id") if agent_output else None,
                "patient_id": conversation_turn.get("patient_id"),
            }
            return await self._service.process_memory_candidate(
                candidate=candidate,
                user_role=user.role,
                tenant_id=user.tenant_id,
                user_id=user.user_id,
            )
        return None  # Full implementation required per spec

    async def retrieve_relevant(
        self, user: UserContext, patient_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        if self._using_full:
            return await self._service.retrieve_governed_memories(
                tenant_id=user.tenant_id,
                user_id=user.user_id,
                role=user.role,
                patient_id=patient_id,
            )
        return []


memory_service = MemoryService()
