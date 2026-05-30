# ClinIQ-Nexus Compliance Architecture

This platform was designed from day one around HIPAA Privacy, Security, and Breach Notification Rules.

## Core Controls Implemented in This Reference

- **Access Control (164.312(a)(1))**: RBAC + ABAC enforced in middleware and MCP. Minimum necessary applied at retrieval time.
- **Audit Controls (164.312(b))**: Every PHI touch, route decision, MCP decision, and human review action produces an immutable `audit_event`.
- **Integrity (164.312(c)(1))**: All clinical source data lives in versioned document chunks. Chat history is minimized.
- **Transmission Security (164.312(e)(1))**: TLS everywhere. In AWS: private VPC + VPC endpoints.
- **Encryption (164.312(a)(2)(iv) & (e)(2)(ii))**: KMS everywhere in production. Local uses volume encryption.
- **Emergency Access (164.312(a)(2)(ii))**: Break-glass workflow exists in the data model and is auditable.
- **Person or Entity Authentication (164.312(d))**: Cognito (prod) / JWT (reference) with strong claims.
- **Automatic Logoff & Activity Monitoring**: Rate limiting + full correlation ID tracing.

## What Is Still Required Before Any Real Deployment

1. Signed BAA with AWS
2. Formal risk analysis (45 CFR 164.308(a)(1))
3. Clinical safety validation board sign-off
4. HITRUST / SOC2 Type II roadmap
5. Real penetration testing + red team (prompt injection, retrieval poisoning, model extraction)
6. Legal review of all patient-facing language
7. Integration with real EHR via FHIR with proper consent management

This reference implementation gives you the **technical architecture** that makes the above controls practical and auditable.

## Philosophy

We believe the only way to build trustworthy clinical AI is to make governance non-bypassable at the architecture level — not through policy documents alone.
