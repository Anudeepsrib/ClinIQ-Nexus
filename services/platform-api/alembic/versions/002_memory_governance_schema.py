"""Expand governed Hindsight Memory schema.

Revision ID: 002
Revises: 001
Create Date: 2026-05-30
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("memory_records") as batch:
        batch.add_column(sa.Column("hospital_id", sa.String(36), nullable=True))
        batch.add_column(sa.Column("facility_id", sa.String(36), nullable=True))
        batch.add_column(sa.Column("role", sa.String(50), nullable=True))
        batch.add_column(sa.Column("encounter_id", sa.String(36), nullable=True))
        batch.add_column(sa.Column("memory_text_minimized", sa.Text(), nullable=True))
        batch.add_column(sa.Column("sensitivity_level", sa.String(30), nullable=True))
        batch.add_column(sa.Column("source_conversation_id", sa.String(36), nullable=True))
        batch.add_column(sa.Column("source_workflow_id", sa.String(36), nullable=True))
        batch.add_column(sa.Column("policy_decision_id", sa.String(36), nullable=True))
        batch.add_column(sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False))
        batch.add_column(sa.Column("audit_event_id", sa.String(36), nullable=True))

    op.create_table(
        "memory_policy_decisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("memory_id", sa.String(36), nullable=True, index=True),
        sa.Column("decision", sa.String(30), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("sensitivity_level", sa.String(30), nullable=True),
        sa.Column("audit_event_id", sa.String(36), nullable=True),
        sa.Column("policy_tags", postgresql.JSONB, default={}),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_memory_records_scope", "memory_records", ["tenant_id", "user_id", "patient_id"])
    op.create_index("ix_memory_records_policy", "memory_records", ["policy_decision_id"])


def downgrade() -> None:
    op.drop_index("ix_memory_records_policy", table_name="memory_records")
    op.drop_index("ix_memory_records_scope", table_name="memory_records")
    op.drop_table("memory_policy_decisions")

    with op.batch_alter_table("memory_records") as batch:
        batch.drop_column("audit_event_id")
        batch.drop_column("is_active")
        batch.drop_column("expires_at")
        batch.drop_column("policy_decision_id")
        batch.drop_column("source_workflow_id")
        batch.drop_column("source_conversation_id")
        batch.drop_column("sensitivity_level")
        batch.drop_column("memory_text_minimized")
        batch.drop_column("encounter_id")
        batch.drop_column("role")
        batch.drop_column("facility_id")
        batch.drop_column("hospital_id")
