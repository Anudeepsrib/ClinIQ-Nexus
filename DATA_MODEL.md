# ClinIQ-Nexus Data Model

## Core Principles

- Every table (except a few reference tables) carries `tenant_id` for isolation.
- Patient-scoped tables also carry `patient_id` for easy ABAC enforcement.
- Audit events are immutable and append-only.
- Chat history is deliberately minimized — raw clinical text lives in `document_chunks`.
- Memory records are explicitly governed and non-clinical.

## Key Tables

- **tenants, hospitals, facilities, departments**: Multi-tenant hierarchy
- **users**: Role + ABAC attributes (assigned patients, departments, break-glass flag)
- **patients + encounters**: Core clinical entities
- **documents + document_chunks**: Primary source of truth for RAG (with rich metadata + vectors)
- **consent_records**: Explicit consent modeling
- **conversations + messages**: Minimized chat history with route, confidence, citations, safety flags
- **audit_events**: The single source of truth for all access and decisions
- **human_review_tasks**: State machine for clinical/legal/compliance review
- **agent_workflows**: Long-running orchestrated work
- **memory_records**: Governed, non-authoritative long-term preferences
- **safety_events**: Clinical risk signals and escalations

## Indexes (Performance Critical)

Heavy indexes exist on:
- tenant_id + patient_id combinations
- created_at for audit and time-based queries
- vector columns (HNSW in pgvector / OpenSearch)

## Migrations

Managed via Alembic. Initial schema is in `alembic/versions/001_initial_schema.py`.

The model is deliberately normalized enough for governance while being practical for RAG retrieval.
