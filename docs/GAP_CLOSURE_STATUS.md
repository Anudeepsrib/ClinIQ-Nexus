# Gap Closure Status

Last updated: 2026-05-30

## Closed In This Pass

- Fixed Python import/package layout for `services.agent_orchestration_service`, `services.memory_service`, and root-level tests.
- Made Deep Agent tools instantiate correctly with LangChain `BaseTool`/Pydantic internals.
- Wired `DeepAgentFactory` audit/memory tools and made discharge planning invoke the Deep Agent path.
- Added an adapter in `BaseDeepAgent` for the official LangChain `deepagents.create_deep_agent` harness when the optional SDK and production model are installed.
- Added missing Hindsight Memory service package files, standalone FastAPI routes, schemas, models, and platform `/api/v1/memory/*` endpoints.
- Expanded memory schema with governed memory fields and `memory_policy_decisions`.
- Fixed memory repository fallback behavior so tests and local runs do not require a running Postgres instance.
- Fixed low-confidence router fallback and admin de-identified MCP handling.
- Prevented `simple_llm` from retrieving PHI.
- Added audit logging/query helpers and audit endpoints for events, access, and model usage.
- Created real review queue entries for chat responses requiring human review.
- Added minimized chat-history persistence with graceful fallback.
- Updated Docker build context so platform-api can import sibling service packages.
- Updated CI so critical tests, Terraform validation, frontend build, and critical Ruff checks are no longer silently ignored.

## Still Not Production-Complete

- Cognito/JWKS validation is not fully implemented; local JWT/demo auth still exists.
- The official `deepagents` SDK is adapter-supported but not pinned into the local requirements because the current repo still pins older LangChain versions.
- Bedrock Claude/Titan providers and OpenSearch hybrid retrieval are still provider abstractions/local implementations, not real AWS clients.
- Terraform modules beyond VPC are still not fully implemented.
- Frontend remains a single consolidated demo experience, not the full required multi-page hospital application.
- Document ingestion still needs full S3 upload, malware scanning, extraction, boilerplate removal, Titan embedding, and OpenSearch indexing.
- Review tasks are still backed by an in-memory queue for the local workflow helper; full DB-backed workflow persistence remains needed.
- OpenTelemetry, CloudWatch dashboards, CloudTrail, WAF, KMS, IAM least privilege, VPC endpoints, and AWS deployment automation remain incomplete.
- Full security/load/frontend/infrastructure test suites remain incomplete.

## Current Verification

- `python -m pytest -q` passes: 20 tests.
- `ruff check --select E9,F63,F7,F82 services/platform-api/app services/memory-service/app services/agent-orchestration-service/app tests` passes.
- `python -c "import app.main; print('backend import ok')"` passes from `services/platform-api`.
- `npm run build` passes from `apps/web`.
