"""Initial schema - full careOS data model.

Revision ID: 001
Revises: 
Create Date: 2026-05-29

This migration creates every table required by the architecture:
tenants, users, patients, encounters, documents, chunks, consent,
conversations, audit, human review, memory, safety events, etc.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tenants
    op.create_table(
        "tenants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Hospitals / Facilities / Departments (simplified for demo)
    op.create_table(
        "hospitals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
    )

    op.create_table(
        "facilities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("hospital_id", sa.String(36), sa.ForeignKey("hospitals.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
    )

    # Users
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, index=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
    )

    # Patients
    op.create_table(
        "patients",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("mrn", sa.String(50), nullable=False, index=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("date_of_birth", sa.Date, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Encounters
    op.create_table(
        "encounters",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("patients.id"), nullable=False, index=True),
        sa.Column("encounter_type", sa.String(50)),
        sa.Column("status", sa.String(30), default="active"),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
    )

    # Documents (raw metadata)
    op.create_table(
        "documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("patients.id"), nullable=True, index=True),
        sa.Column("encounter_id", sa.String(36), sa.ForeignKey("encounters.id"), nullable=True),
        sa.Column("doc_type", sa.String(80), nullable=False, index=True),
        sa.Column("title", sa.String(500)),
        sa.Column("source_system", sa.String(100)),
        sa.Column("s3_key", sa.String(500)),
        sa.Column("sensitivity_level", sa.String(30), default="phi"),
        sa.Column("consent_scope", sa.String(50), default="treatment"),
        sa.Column("author_role", sa.String(50)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Document chunks + vector embeddings (pgvector)
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("documents.id"), nullable=False, index=True),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("patients.id"), nullable=True, index=True),
        sa.Column("encounter_id", sa.String(36), nullable=True),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_normalized", sa.Text()),
        sa.Column("doc_type", sa.String(80)),
        sa.Column("source_system", sa.String(100)),
        sa.Column("sensitivity_level", sa.String(30)),
        sa.Column("consent_scope", sa.String(50)),
        sa.Column("embedding", postgresql.ARRAY(sa.Float).with_variant(sa.dialects.postgresql.ARRAY(sa.Float), "postgresql")),  # will be replaced by vector in real migration
        sa.Column("metadata_json", postgresql.JSONB, default={}),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Add vector column properly (pgvector)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("ALTER TABLE document_chunks ALTER COLUMN embedding TYPE vector(384) USING embedding::vector(384)")

    # Create vector index (HNSW for good recall/speed)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding "
        "ON document_chunks USING hnsw (embedding vector_cosine_ops)"
    )

    # Consent records
    op.create_table(
        "consent_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("scope", sa.String(50), nullable=False),
        sa.Column("granted_to_role", sa.String(50)),
        sa.Column("granted_to_user_id", sa.String(36)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Conversations & Messages (minimized chat history)
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("patients.id"), nullable=True, index=True),
        sa.Column("role", sa.String(50)),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("conversation_id", sa.String(36), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),  # user / assistant / system
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("intent_route", sa.String(50)),
        sa.Column("model_used", sa.String(100)),
        sa.Column("confidence", sa.Float()),
        sa.Column("requires_human_review", sa.Boolean(), default=False),
        sa.Column("safety_flags", postgresql.JSONB, default=[]),
        sa.Column("retrieved_document_ids", postgresql.JSONB, default=[]),
        sa.Column("audit_event_id", sa.String(36)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Audit events (immutable, append-only)
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("event_type", sa.String(80), nullable=False, index=True),
        sa.Column("resource_type", sa.String(50)),
        sa.Column("resource_id", sa.String(36)),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("patients.id"), nullable=True),
        sa.Column("action", sa.String(50)),
        sa.Column("outcome", sa.String(20)),
        sa.Column("details", postgresql.JSONB, default={}),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("user_agent", sa.String(500)),
        sa.Column("correlation_id", sa.String(36)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    )

    # Human review tasks
    op.create_table(
        "human_review_tasks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("workflow_id", sa.String(36)),
        sa.Column("task_type", sa.String(80), nullable=False),
        sa.Column("status", sa.String(30), default="pending_review", index=True),
        sa.Column("priority", sa.String(20), default="medium"),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("patients.id"), nullable=True),
        sa.Column("requested_by_user_id", sa.String(36)),
        sa.Column("assigned_to_role", sa.String(50)),
        sa.Column("reason", sa.Text()),
        sa.Column("context_snapshot", postgresql.JSONB, default={}),
        sa.Column("resolution_notes", sa.Text()),
        sa.Column("resolved_by_user_id", sa.String(36)),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Agent workflows
    op.create_table(
        "agent_workflows",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("workflow_type", sa.String(80), nullable=False),
        sa.Column("status", sa.String(30), default="running"),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("patients.id"), nullable=True),
        sa.Column("initiated_by_user_id", sa.String(36)),
        sa.Column("input_context", postgresql.JSONB, default={}),
        sa.Column("output_context", postgresql.JSONB, default={}),
        sa.Column("requires_human_review", sa.Boolean(), default=False),
        sa.Column("review_task_id", sa.String(36), sa.ForeignKey("human_review_tasks.id")),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )

    # Memory records (governed, non-source-of-truth)
    op.create_table(
        "memory_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("patients.id"), nullable=True),
        sa.Column("memory_type", sa.String(50)),  # preference, workflow_note, etc.
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source", sa.String(50)),
        sa.Column("governance_decision", postgresql.JSONB, default={}),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Safety events
    op.create_table(
        "safety_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("patients.id"), nullable=True),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("severity", sa.String(20)),
        sa.Column("description", sa.Text()),
        sa.Column("triggered_by_route", sa.String(50)),
        sa.Column("human_review_triggered", sa.Boolean(), default=False),
        sa.Column("details", postgresql.JSONB, default={}),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Rate limit events (for analytics)
    op.create_table(
        "rate_limit_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("endpoint", sa.String(200)),
        sa.Column("limit", sa.Integer()),
        sa.Column("window_seconds", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Indexes for performance (critical for RAG + audit queries)
    op.create_index("ix_document_chunks_tenant_patient", "document_chunks", ["tenant_id", "patient_id"])
    op.create_index("ix_audit_events_tenant_created", "audit_events", ["tenant_id", "created_at"])
    op.create_index("ix_messages_conversation_created", "messages", ["conversation_id", "created_at"])
    op.create_index("ix_human_review_status_tenant", "human_review_tasks", ["tenant_id", "status"])


def downgrade() -> None:
    op.drop_table("rate_limit_events")
    op.drop_table("safety_events")
    op.drop_table("memory_records")
    op.drop_table("agent_workflows")
    op.drop_table("human_review_tasks")
    op.drop_table("audit_events")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("consent_records")
    op.drop_table("document_chunks")
    op.drop_table("documents")
    op.drop_table("encounters")
    op.drop_table("patients")
    op.drop_table("users")
    op.drop_table("facilities")
    op.drop_table("hospitals")
    op.drop_table("tenants")
