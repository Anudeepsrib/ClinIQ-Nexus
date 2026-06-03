# careOS Runbook

## Common Operations

### Restart Everything Clean
```bash
docker compose down -v
docker compose up --build
```

### Re-seed Demo Data
```bash
docker compose exec platform-api python scripts/seed_demo_data.py
```

### View Logs
```bash
make logs-api
make logs-web
```

### Run Canonical Use Case Demo
```bash
docker compose exec platform-api python scripts/demo_canonical_use_cases.py
```

## Troubleshooting

**"Connection refused" to API from frontend**
- Make sure `docker compose up` completed successfully
- Check that the backend health endpoint returns 200: `curl http://localhost:8000/health`

**No data returned in chat**
- Re-seed the database (see above)
- The demo data is synthetic and scoped to `pat_001` + `tenant_hospital_a`

**Human Review Queue not showing tasks**
- Tasks are only created by agentic workflows (Discharge Planning, Risk Signal, etc.)
- Try running a workflow from the Workflows tab or sidebar buttons

## Production Alerts (Reference)

In a real deployment you would monitor:
- Human review queue depth > threshold
- MCP block rate spikes
- High rate of low-confidence routes
- Unusual cross-department access patterns
- Bedrock / OpenSearch cost anomalies

## Emergency Procedures

- **Break-glass access**: Documented in the data model + audit system. Requires reason + timestamp + approver.
- **Incident response**: All actions are auditable. Preserve correlation IDs.

## Scaling Notes

- Agentic workflows are more expensive and slower — rate limit them more aggressively.
- OpenSearch and Bedrock are the primary cost drivers at scale.
- Consider caching governed context for repeated similar queries within a session (with strict TTL).
