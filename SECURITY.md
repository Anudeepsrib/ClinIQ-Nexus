# careOS Security Model

## Defense in Depth

1. **Network**
   - All services in private subnets
   - No public database or OpenSearch exposure
   - VPC endpoints for AWS services
   - Request size limits + hard timeouts at app layer (enterprise add)

2. **Identity**
   - Amazon Cognito with MFA (production)
   - Strong JWT validation + short-lived tokens (8h aligned)
   - Break-glass process with full audit
   - Secure cookie flags + httpOnly in frontend sessions

3. **Authorization**
   - Mandatory RBAC + ABAC on every request (middleware + per-endpoint)
   - Enhanced tenant isolation middleware with early patient ABAC guards
   - MCP as the final context gate before any LLM call
   - Minimum necessary enforced at retrieval time

4. **Data Protection**
   - KMS encryption everywhere
   - Row-level security patterns available in schema
   - No raw PHI in chat history or logs (enforced + redaction)
   - Structured logging with mandatory PHI/PII redaction processor (keys + regex + truncation)

5. **Application**
   - Strict input/output validation (Pydantic + client bounds)
   - Prompt injection defenses (via MCP + grounding + retrieval poisoning block)
   - Rate limiting at WAF, API Gateway, and application layers (Redis, role-aware, fail-closed in prod)
   - Full correlation ID tracing
   - Request body size limit (default 10MB) + per-request hard timeout (configurable 45s)
   - Non-root containers, .dockerignore, secret-file support (JWT/DATABASE_URL_FILE)
   - Client + server sanitization on chat queries; CSP with prod notes

6. **Monitoring & Response**
   - Immutable audit trail
   - CloudTrail + GuardDuty + Security Hub (production)
   - Real-time alerting on anomalous access patterns
   - CI: SAST (bandit), dependency vuln scan (pip-audit/npm-audit), IaC/container lint (hadolint/trivy), secret pattern scan

## Key Invariants (Never Compromised)

- No path exists from user input to LLM without passing through MCP.
- No clinical data leaves the tenant boundary.
- No agent or LLM ever selects its own route.
- Human review is a hard gate for all safety-sensitive workflows.

This architecture was designed so that even if one layer fails, the others still protect PHI and patient safety.
