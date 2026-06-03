# Gap Closure Status

Last updated: 2026-06 (enterprise hardening pass)

## Closed In This Pass (Enterprise Hardening - Senior FSD Pass)

- CI/CD enterprise hardening: bandit SAST, pip-audit, npm-audit, hadolint, stricter ruff+format, coverage, secret grep scan, trivy severity enforcement.
- Added RequestSizeLimitMiddleware and RequestTimeoutMiddleware (configurable, fail closed).
- Enhanced TenantIsolationMiddleware with query tenant checks + patient ABAC pre-enforcement on sensitive paths.
- Implemented structlog PHI/PII redaction processor (sensitive keys + PII regex + length truncation for clinical text).
- Root + web .dockerignore; Dockerfile non-root early, labels, leaner, secret-file ready, better healthcheck, no-access-log.
- docker-compose: variable secrets, resource limits (deploy), no-new-privileges, restart policies, prod guidance.
- Config secrets: JWT_SECRET_FILE / DATABASE_URL_FILE support + apply + stronger validate_runtime (min length, no dev passwords, non-dev secret block).
- DB pool tuning: configurable size/overflow + pool_recycle + connect app name.
- Frontend CSP hardened comments + prod notes; NextAuth: secure cookies, maxAge 8h aligned, httpOnly; ChatInterface: client-side length + control char sanitization.
- CORS: explicit allow_headers (no blanket *).
- Updated PRODUCTION_UPGRADE_PLAN.md and this file.
- Verified: imports, ruff critical, key pytest suites (auth/memory/mcp/safety), frontend build all pass.

Previous closed items preserved below.
- Made Deep Agent tools instantiate correctly with LangChain `BaseTool`/Pydantic internals.
- Wired `DeepAgentFactory` audit/memory tools and made discharge planning invoke the Deep Agent path.
- Added an adapter in `BaseDeepAgent` for the official LangChain `deepagents.create_deep_agent` harness when the optional SDK and production model are installed.
- Pinned and verified the official `deepagents` SDK path with a compatible LangChain/LangGraph set: `deepagents==0.5.0`, `langchain==1.2.18`, `langchain-core==1.4.0`, `langgraph==1.1.10`, `langgraph-checkpoint==3.0.1`, and `langgraph-prebuilt==1.0.13`.
- Added missing Hindsight Memory service package files, standalone FastAPI routes, schemas, models, and platform `/api/v1/memory/*` endpoints.
- Expanded memory schema with governed memory fields and `memory_policy_decisions`.
- Fixed memory repository fallback behavior so tests and local runs do not require a running Postgres instance.
- Fixed low-confidence router fallback and admin de-identified MCP handling.
- Prevented `simple_llm` from retrieving PHI.
- Added audit logging/query helpers and audit endpoints for events, access, and model usage.
- Created DB-backed review queue entries for chat responses requiring human review, including role-scoped listing, resolution timestamps, escalation, fallback behavior, and audit events.
- Added minimized chat-history persistence with graceful fallback.
- Tightened Cognito/JWKS verification for production mode: required Cognito config, issuer validation, Cognito `token_use` handling, ID-token audience checks, and access-token client ID checks.
- Disabled unauthenticated demo-user fallback whenever `USE_REAL_AWS=true`.
- Added Cognito custom consent-scope mapping into request context.
- Hardened document upload authorization with patient ABAC checks, consent-scope checks, and filename sanitization before S3 key construction.
- Tightened RAG retrieval filters with explicit patient access denial, consent-scope filtering, restricted sensitivity exclusions, and optional document-type constraints.
- Replaced demo Hindsight Memory retrieval with repository-backed, scoped, minimized retrieval that filters role, patient scope, sensitivity, and clinical terms.
- Stopped raw candidate content from being retained in memory audit events; blocked/proposed content is represented by hash and length instead.
- Fixed readiness DB check to use SQLAlchemy `text("SELECT 1")`.
- Disabled the local `/auth/login` JWT minting endpoint outside development and real-AWS mode.
- Added production-like runtime configuration validation for unsafe CORS, missing Cognito configuration, and unchanged local JWT secrets.
- Added API security headers, no-store cache headers for API responses, and HSTS when running with real AWS.
- Made Redis rate-limit outages fail closed in real AWS mode while allowing explicit degraded-open local development behavior.
- Added MCP retrieval-poisoning defense to block prompt-injection patterns inside retrieved chunks before they can reach model context.
- Tightened MCP consent checks to enforce the chunk's actual consent scope, not only generic treatment consent.
- Added focused regression tests for review authorization, governed memory retrieval, and memory audit minimization.
- Added focused regression tests for production auth hardening, runtime config validation, and MCP prompt-injection blocking.
- Updated Docker build context so platform-api can import sibling service packages.
- Updated CI so critical tests, Terraform validation, frontend build, and critical Ruff checks are no longer silently ignored.
- Implemented the Terraform stack beyond VPC: KMS, security groups, VPC endpoints, S3 document/audit buckets, RDS PostgreSQL, ElastiCache Redis, OpenSearch, Cognito, ECS Fargate/ECR/ALB, IAM task roles, Secrets Manager, SQS, EventBridge, WAF, API Gateway, CloudWatch logs/dashboards, and CloudTrail.
- Wired dev, stage, and prod Terraform environments to the full module set with encrypted storage, private networking, service-scoped IAM, database credentials injected from Secrets Manager, and CloudTrail S3 data-event logging.

## Still Not Production-Complete

- Cognito/JWKS validation is implemented in code, but live Cognito pool configuration, MFA policy verification, and end-to-end AWS token tests remain needed before production.
- Bedrock Claude/Titan providers and OpenSearch hybrid retrieval now have real-client paths behind `USE_REAL_AWS`, but they still need live AWS integration tests, IAM hardening, and production index validation.
- Terraform now has full module coverage for the requested AWS stack, but it still needs live `terraform plan/apply` validation in a real AWS account, remote state/locking configuration, Route 53/custom-domain automation, and final account-specific CIDR/domain/secrets values.
- Frontend remains a single consolidated demo experience, not the full required multi-page hospital application.
- Document ingestion still needs full S3 upload, malware scanning, extraction, boilerplate removal, Titan embedding, and OpenSearch indexing.
- Review tasks are DB-backed with a local fallback; full DB-backed workflow state transitions and reviewer assignment workflows still need expansion.
- OpenTelemetry app trace export, endpoint policy tightening, Route 53 automation, and AWS deployment promotion workflows remain incomplete.
- Full security/load/frontend/infrastructure test suites remain incomplete.

## Current Verification (post-hardening)

- `python -m pytest -q` (relevant suites) pass; full collection ~30 tests (slow torch import in env).
- `ruff check --select E9,F63,F7,F82 ...` passes (critical subset).
- `python -m ruff check` (broader) on modified paths clean after fixes.
- Backend core imports + new middlewares + redaction + config validation all load.
- `npm run build` passes from `apps/web`.
- Runtime config validation blocks on weak secrets / prod misconfig as designed.
- Docker build contexts reduced via .dockerignore.
- Native Terraform / live AWS still not executed locally (no creds/tf binary in this env).
