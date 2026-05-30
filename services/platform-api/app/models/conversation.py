from sqlalchemy import String, ForeignKey, Text, Float, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Conversation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "conversations"
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    patient_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("patients.id"), index=True)
    role: Mapped[str | None] = mapped_column(String(50))


class Message(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "messages"
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id"))
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    intent_route: Mapped[str | None] = mapped_column(String(50))
    model_used: Mapped[str | None] = mapped_column(String(100))
    confidence: Mapped[float | None] = mapped_column(Float)
    requires_human_review: Mapped[bool] = mapped_column(Boolean, default=False)
    safety_flags: Mapped[list] = mapped_column(JSONB, default=[])
    retrieved_document_ids: Mapped[list] = mapped_column(JSONB, default=[])
    audit_event_id: Mapped[str | None] = mapped_column(String(36))
