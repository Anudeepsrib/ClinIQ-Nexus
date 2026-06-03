"""
BaseDeepAgent - Foundation for all LangChain Deep Agents in careOS.

This implements the core Deep Agent pattern (Planner + Executor + Critic style)
while enforcing careOS's strict governance requirements:
- All LLM calls go through MCP first
- Only scoped tools are available
- Tenant + role isolation is enforced
- Memory access is always governed
- Human review triggers are respected
- No raw PHI logging
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from langchain_core.tools import BaseTool

try:
    from deepagents import create_deep_agent
except Exception:  # pragma: no cover - optional SDK in local reference envs
    create_deep_agent = None


@dataclass
class DeepAgentContext:
    """Context passed to every Deep Agent."""
    tenant_id: str
    hospital_id: Optional[str]
    facility_id: Optional[str]
    user_id: str
    role: str
    patient_id: Optional[str] = None
    encounter_id: Optional[str] = None
    permissions: List[str] = field(default_factory=list)
    workflow_id: Optional[str] = None
    correlation_id: Optional[str] = None


@dataclass
class DeepAgentOutput:
    """Standardized output from any Deep Agent."""
    workflow_id: str
    route: str
    summary: str
    findings: List[Dict[str, Any]] = field(default_factory=list)
    citations: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    requires_human_review: bool = True
    human_review_reason: str = ""
    safety_flags: List[str] = field(default_factory=list)
    memory_candidates: List[Dict[str, Any]] = field(default_factory=list)
    audit_event_ids: List[str] = field(default_factory=list)
    sub_agent_steps: List[Dict[str, Any]] = field(default_factory=list)  # Trace of planner/executor steps


class BaseDeepAgent(ABC):
    """
    Abstract base for all careOS Deep Agents.
    Every Deep Agent must:
    - Declare its allowed tools (least privilege)
    - Declare required MCP context types
    - Support memory proposal (but never direct writes)
    - Return structured DeepAgentOutput
    """

    def __init__(self, context: DeepAgentContext):
        self.context = context
        self._tools: List[BaseTool] = []
        self._allowed_tool_names: List[str] = []

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name of this Deep Agent (e.g. 'discharge_planning_deep_agent')."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    def allowed_tools(self) -> List[BaseTool]:
        return self._tools

    def register_tool(self, tool: BaseTool, require_mcp_approval: bool = True) -> None:
        """Register a tool. Tools that touch PHI should require MCP approval."""
        if tool.name in self._allowed_tool_names:
            return
        self._tools.append(tool)
        self._allowed_tool_names.append(tool.name)

    @property
    def langchain_deepagents_sdk_available(self) -> bool:
        """Whether the official LangChain Deep Agents SDK is installed."""
        return create_deep_agent is not None

    def build_langchain_deep_agent(
        self,
        system_prompt: str,
        model: Any = None,
        interrupt_on: Optional[Dict[str, Any]] = None,
        checkpointer: Any = None,
        memory: Optional[List[str]] = None,
        store: Any = None,
    ) -> Any:
        """
        Build the official LangChain Deep Agent harness when the optional
        `deepagents` package is installed.

        Local tests use deterministic governed fallbacks so CI does not need
        network/model credentials. Production deployments should install and
        configure `deepagents` plus the Bedrock-backed chat model.
        """
        if create_deep_agent is None:
            return None
        if interrupt_on is None:
            default_interrupts = {
                "propose_memory_candidate": {"allowed_decisions": ["approve", "reject"]},
                "create_human_review_task": False,
                "audit_memory_event": False,
                "classify_memory_candidate": False,
                "retrieve_governed_memory": False,
                "governed_rag_search": False,
            }
            tool_names = set(self._allowed_tool_names)
            interrupt_on = {
                name: config
                for name, config in default_interrupts.items()
                if name in tool_names
            }
        if checkpointer is None and interrupt_on:
            try:
                from langgraph.checkpoint.memory import MemorySaver

                checkpointer = MemorySaver()
            except Exception:
                checkpointer = None
        return create_deep_agent(
            model=model,
            tools=self.allowed_tools,
            system_prompt=system_prompt,
            interrupt_on=interrupt_on,
            checkpointer=checkpointer,
            memory=memory,
            store=store,
        )

    @abstractmethod
    async def run(self, task: str, governed_context: List[Dict[str, Any]]) -> DeepAgentOutput:
        """
        Execute the Deep Agent.

        IMPORTANT: governed_context has ALREADY passed through MCP.
        The Deep Agent must never call raw RAG or memory without going through governance again.
        """
        pass

    def propose_memory_candidate(self, content: str, memory_type: str) -> Dict[str, Any]:
        """Helper to propose a memory candidate (will be governed later)."""
        return {
            "proposed_by": self.name,
            "memory_type": memory_type,
            "content": content,
            "tenant_id": self.context.tenant_id,
            "user_id": self.context.user_id,
            "role": self.context.role,
            "patient_id": self.context.patient_id,
        }
