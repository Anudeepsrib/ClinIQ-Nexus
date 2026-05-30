from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AuditEvent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "audit_events"
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"))
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    resource_type: Mapped[str | None] = mapped_column(String(50))
    resource_id: Mapped[str | None] = mapped_column(String(36))
    patient_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("patients.id"))
    action: Mapped[str | None] = mapped_column(String(50))
    outcome: Mapped[str | None] = mapped_column(String(20))
    details: Mapped[dict] = mapped_column(JSONB, default={})
    ip_address: Mapped[str | None] = mapped_column(String(45))
    correlation_id: Mapped[str | None] = mapped_column(String(36))


class ConsentRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "consent_records"
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"))
    scope: Mapped[str] = mapped_column(String(50))
    granted_to_role: Mapped[str | None] = mapped_column(String(50))
    granted_to_user_id: Mapped[str | None] = mapped_column(String(36))
