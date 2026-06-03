# MediCore AI Platform - Production Upgrade Plan

## Phase 1: Security and Authentication ✅ COMPLETE
- [x] Implement AWS Cognito JWT validation using JWKS in `security.py`
- [x] Add caching for JWKS to avoid frequent external calls
- [x] Enforce ABAC/RBAC across core middleware
- [x] Configure `USE_REAL_AWS` feature flag to toggle Cognito verification
- [x] Terraform modules for AWS Cognito User Pool and App Client

## Phase 2: RAG, Storage, and Real Providers ✅ COMPLETE
- [x] Integrate Amazon OpenSearch client for hybrid retrieval (k-NN + BM25)
- [x] Integrate AWS Bedrock (Claude 3.5 Sonnet via Converse API)
- [x] Integrate Amazon Titan Text Embeddings V2 via Bedrock
- [x] S3 ingestion endpoint with malware scan hooks and file validation
- [x] Terraform modules for OpenSearch, S3

## Phase 3: Workflows, Governance, and MCP ✅ COMPLETE
- [x] PostgreSQL-backed Human-in-the-Loop review queue (replaced in-memory)
- [x] All callers (`chat.py`, `chart_summary.py`, `clinical_risk_signal.py`, `discharge_planning.py`) updated to async DB review creation
- [x] Tenant isolation enforced in all review queue operations
- [x] Role-based visibility filtering in review queue queries

## Phase 4: Frontend and Observability ✅ COMPLETE
- [x] NextAuth Cognito provider (OAuth 2.0 PKCE)
- [x] Unified `useAuth` hook supporting both Cognito SSO and demo mode
- [x] Production sign-in page with Cognito SSO + demo fallback
- [x] Session-based JWT passthrough to platform-api
- [x] MediCore AI branding throughout frontend
- [x] OpenTelemetry instrumentation (TracerProvider, FastAPIInstrumentor, OTLP exporter)
- [x] Terraform modules for CloudWatch Log Groups and CloudTrail audit trail
- [x] Frontend `.env.example` for Cognito configuration

## Phase 5: CI/CD and Final Polish ✅ HARDENED (this pass)
- [x] Expanded GitHub Actions: stricter ruff (incl E,F,W,I etc), ruff format check, bandit SAST, pip-audit (high+), npm audit (high+), hadolint Docker lint, trivy severity HIGH/CRITICAL block, basic secret pattern scan, coverage reporting.
- [x] Added enterprise middleware: RequestSizeLimit (10MB default, configurable), RequestTimeout (45s), enhanced TenantIsolation with early ABAC/path guards.
- [x] PHI/PII redaction processor in structlog (key + regex patterns + truncation for long clinical text).
- [x] Docker hardening: .dockerignore root+web, improved non-root (uid 1001 early), labels, minimal system pkgs, secret file support, health on /ready, --no-access-log, resource hints in compose.
- [x] docker-compose: env var driven secrets, deploy resource limits, security_opt no-new-privs, restart policies, prod comments.
- [x] Config: *_FILE secret support (JWT/DATABASE), stronger runtime validation (secret length, no dev pw in prod-like, env checks), DB pool configurable + recycle.
- [x] Frontend: CSP comments for nonce path, hardened NextAuth (jwt maxAge, secure cookies in prod, httpOnly, session align to 8h), client query sanitization + maxLength.
- [x] CORS tightened (explicit headers, not *).
- [x] DB engine: pool_recycle + app name.
- [ ] (remaining) Live AWS integration tests + e2e full flows, full multi-page frontend, complete ingestion worker.

See GAP_CLOSURE_STATUS.md for updated status.
