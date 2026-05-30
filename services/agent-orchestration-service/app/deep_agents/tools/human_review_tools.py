"""
Human Review Tool — now creates real HumanReviewTask records.
"""

from __future__ import annotations

from typing import Any, Dict
import asyncio
import uuid
import sys
from pathlib import Path
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from ..base_deep_agent import DeepAgentContext

PLATFORM_ROOT = Path(__file__).resolve().parents[6] / "platform-api"
if str(PLATFORM_ROOT) not in sys.path:
    sys.path.insert(0, str(PLATFORM_ROOT))

try:
    from app.models.workflow import HumanReviewTask
    from app.db.session import async_session
    REAL_DB_AVAILABLE = True
except Exception:
    REAL_DB_AVAILABLE = False
    HumanReviewTask = None
    async_session = None


class CreateHumanReviewTaskInput(BaseModel):
    reason: str = Field(..., description="Clear justification for requiring human review")
    priority: str = Field(default="medium", description="low | medium | high")


class CreateHumanReviewTaskTool(BaseTool):
    name: str = "create_human_review_task"
    description: str = "Create a human review task when blockers, risk signals, or low confidence are detected. This pauses the workflow."
    args_schema: type[BaseModel] = CreateHumanReviewTaskInput

    def __init__(self, context: DeepAgentContext):
        super().__init__()
        self.context = context

    async def _arun(self, reason: str, priority: str = "medium", **kwargs: Any) -> Dict[str, Any]:
        if not REAL_DB_AVAILABLE or not HumanReviewTask:
            return {
                "status": "task_created_simulated",
                "reason": reason,
                "priority": priority,
                "note": "Database not available in this environment"
            }

        task_id = f"rev_{uuid.uuid4().hex[:12]}"

        async with async_session() as session:
            task = HumanReviewTask(
                id=task_id,
                tenant_id=self.context.tenant_id,
                task_type="deep_agent_request",
                status="pending_review",
                priority=priority,
                patient_id=self.context.patient_id,
                requested_by_user_id=self.context.user_id,
                assigned_to_role=self.context.role if self.context.role in ["clinician", "care_coordinator"] else "clinician",
                reason=reason,
                context_snapshot={
                    "workflow_id": self.context.workflow_id,
                    "agent": "deep_agent",
                    "tenant_id": self.context.tenant_id,
                },
            )
            session.add(task)
            await session.commit()

        return {
            "status": "human_review_task_created",
            "review_task_id": task_id,
            "reason": reason,
            "priority": priority,
            "assigned_to_role": task.assigned_to_role,
        }

    def _run(self, reason: str, priority: str = "medium", **kwargs: Any) -> Dict[str, Any]:
        return asyncio.run(self._arun(reason, priority))
