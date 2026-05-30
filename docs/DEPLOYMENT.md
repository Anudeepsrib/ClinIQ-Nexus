# ClinIQ-Nexus Deployment Guide

## Local Development (Recommended for Demos & Development)

```bash
git clone <repo>
cd ClinIQ-Nexus
cp .env.example .env
docker compose up --build
```

This will:
- Start PostgreSQL + pgvector
- Start Redis
- Run Alembic migrations
- Seed rich demo data (Maria Gonzalez + multiple document types)
- Start the FastAPI backend
- Start the Next.js frontend

Access:
- Frontend: http://localhost:3000
- API: http://localhost:8000/docs

Demo users are listed in the root README.

## Production Deployment on AWS

### Prerequisites
- AWS account with appropriate permissions
- Terraform >= 1.6
- Domain + Route53 (optional but recommended)
- Secrets configured in AWS Secrets Manager

### High-Level Architecture
- **Compute**: ECS Fargate (platform-api + Next.js)
- **Data**: RDS PostgreSQL + OpenSearch Serverless or managed
- **Auth**: Amazon Cognito
- **Storage**: S3 + KMS
- **Networking**: Private subnets + VPC endpoints
- **Security**: WAF, GuardDuty, Security Hub, CloudTrail

### Step-by-Step (Reference)

1. **Bootstrap Terraform State**
   ```bash
   cd infra/terraform/envs/prod
   terraform init -backend-config=backend.conf
   ```

2. **Deploy Core Infrastructure**
   ```bash
   terraform apply -target=module.vpc -target=module.kms -target=module.cognito
   ```

3. **Deploy Data Layer**
   ```bash
   terraform apply -target=module.rds -target=module.opensearch
   ```

4. **Deploy Application Layer**
   ```bash
   terraform apply
   ```

5. **Seed Production Data**
   - Use the ingestion service with real hospital data sources (FHIR, HL7, PDF exports)
   - Never seed real PHI without proper legal and compliance approval

6. **Configure Cognito**
   - Set up User Pools + Identity Pools
   - Configure SAML/OIDC federation with hospital IdP (Epic, Cerner, Okta, etc.)
   - Enable MFA

### Important Production Considerations

- **HIPAA BAA**: Must be signed with AWS before any PHI is processed.
- **Model Access**: Request Bedrock model access (Claude 3.5 Sonnet, Haiku, Titan embeddings) in the target regions.
- **Cost Control**: Set up budgets + alerts. Bedrock + OpenSearch can become expensive at scale.
- **Clinical Validation**: This reference implementation must go through formal clinical safety review before any real use.
- **Break-Glass**: Implement and test the emergency access workflow.
- **Audit Retention**: Configure long-term archival of `audit_events` to S3 Glacier.

### Recommended Promotion Path
`dev` (LocalStack or small AWS) → `stage` (full stack, synthetic data) → `prod`

## CI/CD

GitHub Actions are configured in `.github/workflows/`.

- PRs run: lint, type checks, unit tests, security scans, Terraform validate/plan
- `dev` deploys automatically on merge to main
- `stage` and `prod` require manual approval gates

## Monitoring & Observability

- CloudWatch Dashboards (cost, latency, error rate, MCP block rate, human review queue depth)
- OpenTelemetry traces propagated across services
- Structured JSON logs with correlation IDs

## Rollback Strategy

- ECS deployments use blue/green or canary via CodeDeploy or ECS deployment controller.
- Database changes must be backward compatible or use expand/contract migration patterns.

---

**This platform is a reference implementation. Real production deployment requires significant additional work in legal, compliance, clinical validation, and operational readiness.**
