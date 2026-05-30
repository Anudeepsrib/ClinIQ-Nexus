from sqlalchemy import Boolean, DateTime, String, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class MemoryRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "memory_records"
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"))
    hospital_id: Mapped[str | None] = mapped_column(String(36))
    facility_id: Mapped[str | None] = mapped_column(String(36))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    role: Mapped[str | None] = mapped_column(String(50))
    patient_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("patients.id"))
    encounter_id: Mapped[str | None] = mapped_column(String(36))
    memory_type: Mapped[str | None] = mapped_column(String(50))
    memory_text_minimized: Mapped[str | None] = mapped_column(Text)
    sensitivity_level: Mapped[str | None] = mapped_column(String(30))
    source_conversation_id: Mapped[str | None] = mapped_column(String(36))
    source_workflow_id: Mapped[str | None] = mapped_column(String(36))
    policy_decision_id: Mapped[str | None] = mapped_column(String(36))
    expires_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    audit_event_id: Mapped[str | None] = mapped_column(String(36))
    content: Mapped[str] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(50))
    governance_decision: Mapped[dict] = mapped_column(JSONB, default={})


class MemoryPolicyDecision(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "memory_policy_decisions"
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    memory_id: Mapped[str | None] = mapped_column(String(36), index=True)
    decision: Mapped[str] = mapped_column(String(30))
    reason: Mapped[str | None] = mapped_column(Text)
    sensitivity_level: Mapped[str | None] = mapped_column(String(30))
    audit_event_id: Mapped[str | None] = mapped_column(String(36))
    policy_tags: Mapped[dict] = mapped_column(JSONB, default={})
