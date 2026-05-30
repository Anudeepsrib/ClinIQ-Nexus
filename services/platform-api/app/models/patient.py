from datetime import date
from sqlalchemy import String, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Patient(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "patients"
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True)
    mrn: Mapped[str] = mapped_column(String(50), index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    date_of_birth: Mapped[date | None] = mapped_column(Date)


class Encounter(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "encounters"
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"))
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), index=True)
    encounter_type: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(30), default="active")
