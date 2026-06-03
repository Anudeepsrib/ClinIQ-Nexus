# careOS API Reference

## Authentication

All protected endpoints require a Bearer JWT.

In local/demo mode you can also use the `X-Demo-User` header.

Login:
```http
POST /api/v1/auth/login
{
  "email": "clinician@hospital-a.demo"
}
```

Response contains `access_token`.

## Core Endpoints

### AI / Chat (Primary Interface)

**Classify Intent**
```http
POST /api/v1/ai/route
{
  "query": "Summarize this patient’s last 72 hours before rounds.",
  "patient_id": "pat_001"
}
```

**Main Chat (Recommended)**
```http
POST /api/v1/ai/chat
{
  "query": "...",
  "patient_id": "pat_001"
}
```

Returns:
- `response`
- `route` (simple_rag, discharge_planning, clinical_safety_triage, etc.)
- `confidence`
- `requires_human_review`
- `citations[]`
- `safety_flags[]`
- `human_review_task_id` (if applicable)
- `memory_used`

**Streaming**
```http
POST /api/v1/ai/stream
```
Server-Sent Events with `chunk`, `route`, `mcp`, `done` events.

### Workflows (Agentic)

**72h Clinician Chart Summary**
```http
POST /api/v1/workflows/chart-summary
{
  "patient_id": "pat_001",
  "query": "Summarize last 72 hours before rounds"
}
```

**Discharge Planning**
```http
POST /api/v1/workflows/discharge-planning
```

**Clinical Risk Signal Detection**
```http
POST /api/v1/workflows/risk-signal
```

### Human Review

**List Reviews** (role-filtered)
```http
GET /api/v1/reviews/
```

**Approve / Reject**
```http
POST /api/v1/reviews/{review_id}/approve
{
  "notes": "Approved after chart review"
}
```

### Patients & Documents

Basic CRUD + ingestion endpoints exist. Full details in the OpenAPI spec at `/docs`.

## Error Responses

All errors follow this shape:
```json
{
  "error": "mcp_blocked | forbidden | safety_violation | ...",
  "message": "Human readable message",
  "correlation_id": "..."
}
```

## Rate Limits

- Patients: 20 req/min
- Clinicians/Nurses: 80 req/min
- Agentic workflows: stricter token-based limits

Limits are enforced at WAF + application layer using Redis.

## Versioning

All current endpoints are under `/api/v1`. Future breaking changes will go under `/api/v2`.
