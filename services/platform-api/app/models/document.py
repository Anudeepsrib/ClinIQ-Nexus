from sqlalchemy import String, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

# pgvector support - will be handled by migration
try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    Vector = None  # type: ignore



class Document(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "documents"
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    patient_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("patients.id"), index=True)
    encounter_id: Mapped[str | None] = mapped_column(String(36))
    doc_type: Mapped[str] = mapped_column(String(80), index=True)
    title: Mapped[str | None] = mapped_column(String(500))
    source_system: Mapped[str | None] = mapped_column(String(100))
    s3_key: Mapped[str | None] = mapped_column(String(500))
    sensitivity_level: Mapped[str] = mapped_column(String(30), default="phi")
    consent_scope: Mapped[str] = mapped_column(String(50), default="treatment")
    author_role: Mapped[str | None] = mapped_column(String(50))


class DocumentChunk(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "document_chunks"
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), index=True)
    patient_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("patients.id"), index=True)
    encounter_id: Mapped[str | None] = mapped_column(String(36))
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    content_normalized: Mapped[str | None] = mapped_column(Text)
    doc_type: Mapped[str | None] = mapped_column(String(80))
    sensitivity_level: Mapped[str | None] = mapped_column(String(30))
    consent_scope: Mapped[str | None] = mapped_column(String(50))
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384) if Vector else JSONB, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default={})
