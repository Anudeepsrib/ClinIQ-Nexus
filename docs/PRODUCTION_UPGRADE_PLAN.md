# MediCore AI Platform - Production Upgrade Plan

## Phase 1: Security and Authentication (Current)
- [ ] Implement AWS Cognito JWT validation using JWKS in `security.py`
- [ ] Add caching for JWKS to avoid frequent external calls
- [ ] Enforce ABAC/RBAC across core middleware
- [ ] Configure `USE_REAL_AWS` feature flag to toggle Cognito verification
- [ ] Terraform modules for AWS Cognito User Pool and App Client

## Phase 2: RAG, Storage, and Real Providers
- [ ] Integrate Amazon OpenSearch client for hybrid retrieval
- [ ] Integrate AWS Bedrock (Claude 3.5 Sonnet, Haiku, Titan Embeddings) via boto3
- [ ] S3 ingestion endpoint with malware scan hooks and boilerplate removal
- [ ] Terraform modules for OpenSearch, Bedrock, S3

## Phase 3: Workflows, Governance, and MCP
- [ ] Refactor `ModelRouter` to enforce MCP/Context Governance
- [ ] Deep Agents for Discharge Planning and Safety Triage using LangGraph
- [ ] Integrate Human-in-the-loop review queue backed by Postgres

## Phase 4: Frontend and Observability
- [ ] Connect Next.js with Cognito
- [ ] Add OpenTelemetry hooks to FastAPI
- [ ] Create CloudWatch and CloudTrail configurations in Terraform

## Phase 5: CI/CD and Final Polish
- [ ] Update GitHub actions for strict linting/testing
- [ ] Update all Documentation (ARCHITECTURE.md, SECURITY.md, etc.)
