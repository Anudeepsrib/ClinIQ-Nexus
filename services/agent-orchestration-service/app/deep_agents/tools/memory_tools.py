"""
Fully wired Memory Tools for Deep Agents.

These are the only allowed interfaces for Deep Agents to interact with Hindsight Memory.
All operations are governed.
"""

from __future__ import annotations

from typing import Any, Dict, List
import asyncio
import sys
from pathlib import Path
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from ..base_deep_agent import DeepAgentContext

# Bridge to real Hindsight Memory service
MEMORY_SERVICE_ROOT = Path(__file__).resolve().parents[6] / "memory-service"
if str(MEMORY_SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(MEMORY_SERVICE_ROOT))

try:
    from app.services.hindsight_memory_service import HindsightMemoryService
    REAL_MEMORY_SERVICE = HindsightMemoryService()
except Exception:
    REAL_MEMORY_SERVICE = None


class RetrieveGovernedMemoryInput(BaseModel):
    query: str = Field(..., description="What kind of preference, pattern, or workflow note are you looking for?")


class RetrieveGovernedMemoryTool(BaseTool):
    name: str = "retrieve_governed_memory"
    description: str = (
        "Retrieve previously approved, minimized, non-clinical memories for the current user/role/patient context. "
        "Only safe, governed memories are returned."
    )
    args_schema: type[BaseModel] = RetrieveGovernedMemoryInput

    def __init__(self, context: DeepAgentContext):
        super().__init__()
        self.context = context

    async def _arun(self, query: str, **kwargs: Any) -> List[Dict[str, Any]]:
        if not REAL_MEMORY_SERVICE:
            return [{"note": "Hindsight Memory service not available"}]

        return await REAL_MEMORY_SERVICE.retrieve_governed_memories(
            tenant_id=self.context.tenant_id,
            user_id=self.context.user_id,
            role=self.context.role,
            patient_id=self.context.patient_id,
        )

    def _run(self, query: str, **kwargs: Any) -> List[Dict[str, Any]]:
        return asyncio.run(self._arun(query))


class ProposeMemoryCandidateInput(BaseModel):
    content: str = Field(..., description="Non-clinical fact or recurring pattern worth remembering long-term")
    memory_type: str = Field(..., description="preference | workflow_note | formatting_preference")


class ProposeMemoryCandidateTool(BaseTool):
    name: str = "propose_memory_candidate"
    description: str = (
        "Propose a new memory candidate. It will be evaluated by Hindsight Memory governance "
        "(PHI minimization, sensitivity classification, role/consent checks). Only approved memories are stored."
    )
    args_schema: type[BaseModel] = ProposeMemoryCandidateInput

    def __init__(self, context: DeepAgentContext):
        super().__init__()
        self.context = context

    async def _arun(self, content: str, memory_type: str, **kwargs: Any) -> Dict[str, Any]:
        if not REAL_MEMORY_SERVICE:
            return {"status": "proposed_but_not_persisted", "content": content, "memory_type": memory_type}

        candidate = {
            "content": content,
            "memory_type": memory_type,
            "source_workflow_id": self.context.workflow_id,
            "patient_id": self.context.patient_id,
        }

        result = await REAL_MEMORY_SERVICE.process_memory_candidate(
            candidate=candidate,
            user_role=self.context.role,
            tenant_id=self.context.tenant_id,
            user_id=self.context.user_id,
        )
        return result

    def _run(self, content: str, memory_type: str, **kwargs: Any) -> Dict[str, Any]:
        return asyncio.run(self._arun(content, memory_type))
