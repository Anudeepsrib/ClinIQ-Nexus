"""
Audit tools for Deep Agents (especially compliance and operations agents).
"""

from __future__ import annotations

from typing import Any, Dict
import asyncio
import uuid
import sys
from pathlib import Path
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

from ..base_deep_agent import DeepAgentContext

PLATFORM_ROOT = Path(__file__).resolve().parents[4] / "platform-api"
if str(PLATFORM_ROOT) not in sys.path:
    sys.path.insert(0, str(PLATFORM_ROOT))

try:
    from app.models.audit import AuditEvent
    from app.db.session import async_session
    REAL_AUDIT_AVAILABLE = True
except Exception:
    REAL_AUDIT_AVAILABLE = False
    AuditEvent = None
    async_session = None


class LogDeepAgentDecisionInput(BaseModel):
    decision: str = Field(..., description="Summary of the decision or finding")
    confidence: float = Field(..., description="Agent confidence in the finding")
    flags: list[str] = Field(default_factory=list)


class LogDeepAgentDecisionTool(BaseTool):
    name: str = "log_deep_agent_decision"
    description: str = "Log an important decision, finding, or anomaly from a Deep Agent for audit and compliance purposes."
    args_schema: type[BaseModel] = LogDeepAgentDecisionInput
    _context: DeepAgentContext = PrivateAttr()

    def __init__(self, context: DeepAgentContext):
        super().__init__()
        self._context = context

    @property
    def context(self) -> DeepAgentContext:
        return self._context

    async def _arun(self, decision: str, confidence: float, flags: list[str] = None, **kwargs: Any) -> Dict[str, Any]:
        if not REAL_AUDIT_AVAILABLE or not AuditEvent:
            return {
                "status": "logged_simulated",
                "decision": decision,
                "audit_id": "audit_sim_" + uuid.uuid4().hex[:8]
            }

        audit_id = f"audit_{uuid.uuid4().hex[:12]}"

        async with async_session() as session:
            event = AuditEvent(
                id=audit_id,
                tenant_id=self.context.tenant_id,
                user_id=self.context.user_id,
                event_type="deep_agent_decision",
                resource_type="deep_agent",
                resource_id=self.context.workflow_id,
                patient_id=self.context.patient_id,
                action="deep_agent_analysis",
                outcome="success",
                details={
                    "decision": decision,
                    "confidence": confidence,
                    "flags": flags or [],
                    "agent_context": {
                        "role": self.context.role,
                        "route": "deep_agent",
                    }
                },
                correlation_id=self.context.correlation_id,
            )
            session.add(event)
            await session.commit()

        return {
            "status": "audit_event_created",
            "audit_event_id": audit_id,
            "decision": decision,
        }

    def _run(self, decision: str, confidence: float, flags: list[str] = None, **kwargs: Any) -> Dict[str, Any]:
        return asyncio.run(self._arun(decision, confidence, flags))
