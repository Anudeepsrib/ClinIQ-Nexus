"""
Governed RAG Tool for Deep Agents.

This tool is the ONLY way Deep Agents are allowed to retrieve additional context.
It always operates on top of already-governed data and re-applies MCP scoping.
"""

from __future__ import annotations

from typing import Any, Dict, List
import asyncio
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

from ..base_deep_agent import DeepAgentContext

# Bridge to real RAG service
import sys
from pathlib import Path
PLATFORM_API_ROOT = Path(__file__).resolve().parents[4] / "platform-api"
if str(PLATFORM_API_ROOT) not in sys.path:
    sys.path.insert(0, str(PLATFORM_API_ROOT))

try:
    from app.services.rag.service import retrieve_authorized_chunks
    from app.services.mcp.service import MCPContextGovernanceService
    REAL_RAG_AVAILABLE = True
except Exception:
    REAL_RAG_AVAILABLE = False
    retrieve_authorized_chunks = None
    MCPContextGovernanceService = None


class GovernedRAGInput(BaseModel):
    query: str = Field(..., description="Focused query for additional governed clinical context")
    doc_types: List[str] = Field(default_factory=list, description="Optional document type filters (e.g. ['lab_report', 'progress_note'])")


class GovernedRAGTool(BaseTool):
    name: str = "governed_rag_search"
    description: str = (
        "Search within already-authorized and MCP-governed context for this workflow and user. "
        "Use this when you need more specific information from clinical documents. "
        "Never use for raw or unauthorized data."
    )
    args_schema: type[BaseModel] = GovernedRAGInput
    _context: DeepAgentContext = PrivateAttr()
    _mcp: Any = PrivateAttr(default=None)

    def __init__(self, context: DeepAgentContext):
        super().__init__()
        self._context = context
        self._mcp = MCPContextGovernanceService() if MCPContextGovernanceService else None

    @property
    def context(self) -> DeepAgentContext:
        return self._context

    async def _arun(self, query: str, doc_types: List[str] = None, **kwargs: Any) -> List[Dict[str, Any]]:
        if not REAL_RAG_AVAILABLE or not retrieve_authorized_chunks:
            return [{"error": "Real RAG service not available in this environment", "query": query}]

        # Simulate a UserContext-like object for the RAG service
        class _Ctx:
            tenant_id = self.context.tenant_id
            user_id = self.context.user_id
            role = self.context.role
            assigned_patient_ids = {self.context.patient_id} if self.context.patient_id else set()
            can_access_all_patients_in_tenant = self.context.role in ["clinician", "care_coordinator", "admin"]
            consent_scopes = ["treatment", "care_coordination"]

            def can_access_patient(self, pid: str) -> bool:
                if self.can_access_all_patients_in_tenant:
                    return True
                return pid == self.user_id or pid in self.assigned_patient_ids

        ctx = _Ctx()

        # Retrieve with proper ABAC
        chunks = await retrieve_authorized_chunks(
            query=query,
            user=ctx,
            patient_id=self.context.patient_id,
            top_k=6
        )

        # Re-apply MCP governance on the results (defense in depth)
        if self._mcp and chunks:
            decision = await self._mcp.govern(
                candidate_chunks=chunks,
                user=ctx,
                route="deep_agent_rag",
                patient_id=self.context.patient_id,
                query=query,
            )
            chunks = decision.allowed_context

        # Return only safe, minimized content + metadata
        return [
            {
                "chunk_id": c.get("chunk_id"),
                "doc_type": c.get("doc_type"),
                "content": c.get("content", "")[:1200],
                "relevance": c.get("relevance", 0.0),
                "document_id": c.get("document_id"),
            }
            for c in chunks[:5]
        ]

    def _run(self, query: str, doc_types: List[str] = None, **kwargs: Any) -> List[Dict[str, Any]]:
        # Synchronous wrapper for LangChain compatibility
        return asyncio.run(self._arun(query, doc_types))
