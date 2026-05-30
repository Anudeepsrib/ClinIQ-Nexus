# MediCore AI Platform

**Enterprise-Grade, HIPAA-Compliant AI Platform for Hospitals and Health Systems**

MediCore AI Platform is the governed hospital AI platform implemented in this repository. It can sit under a broader hospital application umbrella alongside existing hospital applications such as ClinIQ, ClinIQ-Nexus, and other healthcare tools. The current local product shell still uses some ClinIQ-Nexus labels while the platform services use the MediCore architecture and governance model.

This repository is a production-oriented reference implementation of a multi-tenant clinical AI platform. It demonstrates how hospitals can safely deploy large language models against sensitive patient data while enforcing strict clinical safety, privacy, consent, and governance controls.

> **Critical Clinical Safety Rule**: This system **never** diagnoses, prescribes, or makes final clinical decisions. It summarizes, retrieves, flags risk signals, drafts for review, and always requires human oversight for safety-sensitive outputs.

## What Makes This Different

- **Deterministic Intent Router first** — Agents are never used for routing decisions.
- **Mandatory MCP Context Governance Layer** — No PHI reaches an LLM without explicit minimization, consent enforcement, role adaptation, and human-review flagging.
- **LangGraph-native agentic workflows** with first-class Human-in-the-Loop.
- **Deep defense-in-depth**: RBAC + ABAC + tenant isolation + minimum-necessary + audit on every path.
- **Local runnable in 5 minutes** with production-identical architecture (mocked Bedrock/OpenSearch/Cognito using clean abstractions).

## Quick Start (Local Development) — 5 Minutes

```bash
git clone <this-repo>
cd ClinIQ-Nexus
cp .env.example .env
docker compose up --build
```

**What happens automatically:**
- Postgres + pgvector + Redis start
- Backend runs migrations + seeds rich synthetic clinical data
- Next.js frontend starts

**Access:**
- **Best experience:** http://localhost:3000
- **API docs:** http://localhost:8000/docs

**Demo Users (switch freely):**
- `clinician@hospital-a.demo` — Dr. Sarah Chen
- `patient@hospital-a.demo` — Maria Gonzalez
- `nurse@hospital-a.demo`
- `care_coordinator@hospital-a.demo`
- `admin@hospital-a.demo`
- `compliance@hospital-a.demo`

### Recommended Demo Flow

1. Login as **Clinician** → Ask for 72h chart summary (use sidebar button)
2. Login as **Care Coordinator** → Run the real LangGraph Discharge Planning workflow → Go to Review Queue and approve
3. Login as **Nurse** → Run Clinical Risk Signal Agent
4. Login as **Patient** → Ask about lab results + the chest pain safety question
5. Switch to **Admin** → Ask operational questions

All responses go through the full Intent Router + MCP Governance stack.

See `ARCHITECTURE.md` for the interview-ready deep explanation and `docs/RUNBOOK.md` for operations.

## Architecture Highlights

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full interview-ready explanation covering:
- Why deterministic routing before agents
- How MCP prevents PHI leakage
- How hallucinations are systematically reduced
- RBAC/ABAC + minimum necessary implementation
- Human-in-the-loop design
- LangGraph orchestration patterns
- Production vs local provider abstractions

## Canonical Use Cases (All Implemented)

1. Patient lab summary (simple_rag)
2. Chest pain safety triage (clinical_safety_triage → agentic)
3. 72-hour clinician chart summary
4. Nurse overnight risk signal detection
5. Care coordinator discharge readiness
6. Admin delayed discharge operations intelligence (de-identified)
7. General medical education question (simple_llm)

All routes demonstrate correct governance, citations, disclaimers, and human review triggers where required.

## Repository Structure

```
ClinIQ-Nexus/
├── apps/web/                    # Next.js 15 + TypeScript frontend
├── services/platform-api/       # Primary FastAPI application (all logical services)
├── services/ingestion-worker/   # Document processing service
├── packages/                    # Shared types, utils, config
├── infra/terraform/             # Complete modular AWS infrastructure
├── .github/workflows/           # Full CI/CD (lint, test, security, deploy)
├── docs/                        # All required documentation + 10 Mermaid diagrams
└── tests/                       # Unit, integration, security, load
```

## Status

This is a **reference-grade architectural implementation** designed for:
- Engineering interviews (Principal/Staff level)
- Architecture review boards
- Health system innovation teams evaluating clinical AI
- Educational purposes

It is **not** a production deployment ready for real PHI without significant additional work (see [DEPLOYMENT.md](docs/DEPLOYMENT.md) and PRODUCTION_TODO comments).

See [GAP_CLOSURE_STATUS.md](docs/GAP_CLOSURE_STATUS.md) for the latest implementation-hardening status and remaining production work.

## License & Compliance Notice

For demonstration and educational use only. Any use with real patient data requires:
- Legal/compliance review
- Business Associate Agreements with AWS and any model providers
- Clinical safety validation
- Appropriate IRB/ethics oversight where applicable

---

**Built to the highest standards of clinical AI safety and healthcare compliance architecture.**
