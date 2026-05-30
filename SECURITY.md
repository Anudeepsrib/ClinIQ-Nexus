# ClinIQ-Nexus Security Model

## Defense in Depth

1. **Network**
   - All services in private subnets
   - No public database or OpenSearch exposure
   - VPC endpoints for AWS services

2. **Identity**
   - Amazon Cognito with MFA (production)
   - Strong JWT validation + short-lived tokens
   - Break-glass process with full audit

3. **Authorization**
   - Mandatory RBAC + ABAC on every request
   - MCP as the final context gate before any LLM call
   - Minimum necessary enforced at retrieval time

4. **Data Protection**
   - KMS encryption everywhere
   - Row-level security patterns available in schema
   - No raw PHI in chat history or logs

5. **Application**
   - Strict input/output validation
   - Prompt injection defenses (via MCP + grounding)
   - Rate limiting at WAF, API Gateway, and application layers
   - Full correlation ID tracing

6. **Monitoring & Response**
   - Immutable audit trail
   - CloudTrail + GuardDuty + Security Hub (production)
   - Real-time alerting on anomalous access patterns

## Key Invariants (Never Compromised)

- No path exists from user input to LLM without passing through MCP.
- No clinical data leaves the tenant boundary.
- No agent or LLM ever selects its own route.
- Human review is a hard gate for all safety-sensitive workflows.

This architecture was designed so that even if one layer fails, the others still protect PHI and patient safety.
