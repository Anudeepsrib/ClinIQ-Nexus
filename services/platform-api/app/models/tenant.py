from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Tenant(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "tenants"
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(100), unique=True)


class Hospital(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "hospitals"
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"))
    name: Mapped[str] = mapped_column(String(255))


class Facility(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "facilities"
    hospital_id: Mapped[str] = mapped_column(String(36), ForeignKey("hospitals.id"))
    name: Mapped[str] = mapped_column(String(255))
