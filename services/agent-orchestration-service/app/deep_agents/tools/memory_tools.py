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
from pydantic import BaseModel, Field, PrivateAttr

from ..base_deep_agent import DeepAgentContext

# Bridge to real Hindsight Memory service.
REPO_ROOT = Path(__file__).resolve().parents[5]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from services.memory_service.app.services.hindsight_memory_service import HindsightMemoryService
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
    _context: DeepAgentContext = PrivateAttr()

    def __init__(self, context: DeepAgentContext):
        super().__init__()
        self._context = context

    @property
    def context(self) -> DeepAgentContext:
        return self._context

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
    _context: DeepAgentContext = PrivateAttr()

    def __init__(self, context: DeepAgentContext):
        super().__init__()
        self._context = context

    @property
    def context(self) -> DeepAgentContext:
        return self._context

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


class ClassifyMemoryCandidateInput(BaseModel):
    content: str = Field(..., description="Candidate memory text to classify before any write")
    memory_type: str = Field(default="preference")


class ClassifyMemoryCandidateTool(BaseTool):
    name: str = "classify_memory_candidate"
    description: str = "Classify a memory candidate for type, sensitivity, and clinical-source-of-truth risk."
    args_schema: type[BaseModel] = ClassifyMemoryCandidateInput
    _context: DeepAgentContext = PrivateAttr()

    def __init__(self, context: DeepAgentContext):
        super().__init__()
        self._context = context

    async def _arun(self, content: str, memory_type: str = "preference", **kwargs: Any) -> Dict[str, Any]:
        if not REAL_MEMORY_SERVICE:
            return {"memory_type": memory_type, "sensitivity_level": "unknown", "is_clinical": True}
        return REAL_MEMORY_SERVICE.classifier.classify({"content": content, "memory_type": memory_type})

    def _run(self, content: str, memory_type: str = "preference", **kwargs: Any) -> Dict[str, Any]:
        return asyncio.run(self._arun(content, memory_type))


class WriteApprovedMemoryInput(BaseModel):
    content: str = Field(..., description="Candidate memory text. The service will re-govern before storing.")
    memory_type: str = Field(default="preference")


class WriteApprovedMemoryTool(BaseTool):
    name: str = "write_approved_memory"
    description: str = (
        "Submit a memory candidate to the Hindsight Memory write pipeline. "
        "The tool never writes raw content directly; governance may block it."
    )
    args_schema: type[BaseModel] = WriteApprovedMemoryInput
    _context: DeepAgentContext = PrivateAttr()

    def __init__(self, context: DeepAgentContext):
        super().__init__()
        self._context = context

    @property
    def context(self) -> DeepAgentContext:
        return self._context

    async def _arun(self, content: str, memory_type: str = "preference", **kwargs: Any) -> Dict[str, Any]:
        if not REAL_MEMORY_SERVICE:
            return {"status": "blocked", "reason": "Hindsight Memory service not available"}
        return await REAL_MEMORY_SERVICE.process_memory_candidate(
            candidate={
                "content": content,
                "memory_type": memory_type,
                "source_workflow_id": self.context.workflow_id,
                "patient_id": self.context.patient_id,
            },
            user_role=self.context.role,
            tenant_id=self.context.tenant_id,
            user_id=self.context.user_id,
        )

    def _run(self, content: str, memory_type: str = "preference", **kwargs: Any) -> Dict[str, Any]:
        return asyncio.run(self._arun(content, memory_type))


class AuditMemoryEventInput(BaseModel):
    decision: str = Field(..., description="approved | blocked | retrieved")
    reason: str = Field(default="")


class AuditMemoryEventTool(BaseTool):
    name: str = "audit_memory_event"
    description: str = "Write an audit event for a memory read, proposal, classification, or write decision."
    args_schema: type[BaseModel] = AuditMemoryEventInput
    _context: DeepAgentContext = PrivateAttr()

    def __init__(self, context: DeepAgentContext):
        super().__init__()
        self._context = context

    @property
    def context(self) -> DeepAgentContext:
        return self._context

    async def _arun(self, decision: str, reason: str = "", **kwargs: Any) -> Dict[str, Any]:
        if not REAL_MEMORY_SERVICE:
            return {"status": "audit_unavailable", "decision": decision}
        audit_id = await REAL_MEMORY_SERVICE.audit.log_memory_decision(
            tenant_id=self.context.tenant_id,
            user_id=self.context.user_id,
            decision=decision,
            candidate_content=None,
            minimized_content=None,
            reason=reason,
            policy_tags=["deep_agent_memory_tool"],
        )
        return {"status": "audited", "audit_id": audit_id, "decision": decision}

    def _run(self, decision: str, reason: str = "", **kwargs: Any) -> Dict[str, Any]:
        return asyncio.run(self._arun(decision, reason))
