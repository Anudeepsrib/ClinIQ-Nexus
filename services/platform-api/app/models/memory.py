from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class MemoryRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "memory_records"
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    patient_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("patients.id"))
    memory_type: Mapped[str | None] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(50))
    governance_decision: Mapped[dict] = mapped_column(JSONB, default={})
