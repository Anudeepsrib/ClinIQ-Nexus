# ClinIQ-Nexus Testing Strategy

## Philosophy

We test the **safety architecture** extremely thoroughly because patient safety and PHI protection are non-negotiable.

## Test Categories

### 1. Unit Tests (Critical Safety Paths)

- **Intent Router** (`tests/unit/test_intent_router/`)
  - All deterministic rules
  - Safety keyword overrides
  - Role-based defaults
  - Low confidence fallback behavior

- **MCP Governance** (`tests/unit/test_mcp/`)
  - Tenant isolation
  - Patient ABAC enforcement
  - Consent scope validation
  - Role transformation / redaction
  - Abnormal value detection for patient-facing responses

- **Agent Graphs**
  - State transitions
  - Human review gate triggering
  - Correct use of MCP before any generation

### 2. Integration Tests

- Full chat flow (route → retrieval → MCP → generation → audit)
- Workflow execution with review queue interaction
- Memory governance pipeline

### 3. Security Tests

- Prompt injection attempts
- Retrieval poisoning simulation
- Cross-tenant access attempts
- Privilege escalation via role manipulation

### 4. Load & Chaos

- Simple RAG, agentic workflows, and ingestion under load
- Failure injection on downstream services (Bedrock, OpenSearch)

## Running Tests Locally

```bash
cd services/platform-api
python -m pytest tests/ -v --tb=short
```

In CI, security scans (Bandit, Semgrep, Trivy, npm audit) also run.

## Hallucination & Safety Regression Tests

We maintain a set of "golden" queries that must always produce:
- Correct route
- Proper human review triggers
- No fabrication of clinical facts
- Required disclaimers

These are run on every PR.
