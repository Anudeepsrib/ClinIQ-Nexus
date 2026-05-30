from sqlalchemy import String, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class HumanReviewTask(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "human_review_tasks"
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"))
    workflow_id: Mapped[str | None] = mapped_column(String(36))
    task_type: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30), default="pending_review", index=True)
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    patient_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("patients.id"))
    requested_by_user_id: Mapped[str | None] = mapped_column(String(36))
    assigned_to_role: Mapped[str | None] = mapped_column(String(50))
    reason: Mapped[str | None] = mapped_column(Text)
    context_snapshot: Mapped[dict] = mapped_column(JSONB, default={})
    resolution_notes: Mapped[str | None] = mapped_column(Text)
    resolved_by_user_id: Mapped[str | None] = mapped_column(String(36))


class AgentWorkflow(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "agent_workflows"
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"))
    workflow_type: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30), default="running")
    patient_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("patients.id"))
    initiated_by_user_id: Mapped[str | None] = mapped_column(String(36))
    input_context: Mapped[dict] = mapped_column(JSONB, default={})
    output_context: Mapped[dict] = mapped_column(JSONB, default={})
    requires_human_review: Mapped[bool] = mapped_column(Boolean, default=False)
    review_task_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("human_review_tasks.id"))


class SafetyEvent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "safety_events"
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"))
    patient_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("patients.id"))
    event_type: Mapped[str] = mapped_column(String(80))
    severity: Mapped[str | None] = mapped_column(String(20))
    description: Mapped[str | None] = mapped_column(Text)
    triggered_by_route: Mapped[str | None] = mapped_column(String(50))
    human_review_triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    details: Mapped[dict] = mapped_column(JSONB, default={})
