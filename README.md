# careOS

**Enterprise-Grade, HIPAA-Compliant AI Platform for Hospitals and Health Systems**

careOS is the governed hospital AI platform implemented in this repository. It provides a production-oriented reference implementation for deploying large language models against sensitive patient data while enforcing strict clinical safety, privacy, consent, and governance controls.

The platform is designed as a multi-tenant clinical AI system for hospitals and health systems, with deterministic routing, MCP governance, human review, and auditability built into the core workflow.

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
cd careOS
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

### High-Level System Architecture

```mermaid
%%{init: {'theme': 'dark'}}%%
flowchart TB
    subgraph Client["Client Layer"]
        UI[Next.js Frontend<br/>Role-aware Chat + Review Queue]
    end

    subgraph Platform["careOS Platform API (FastAPI)"]
        direction TB
        Auth[Auth + RBAC/ABAC Middleware]
        Router[Deterministic Intent Router<br/>+ Safety Lexicon]
        MCP[MCP Governance Layer<br/>Non-bypassable PHI Filter]
        RAG[RAG Service<br/>pgvector / OpenSearch]
        subgraph Agents["Agentic Layer"]
            LG[LangGraph State Machines]
            DA[LangChain Deep Agents<br/>(Planner-Executor-Critic)]
        end
        Memory[Hindsight Memory<br/>Governed + Audited]
        Review[Human Review State Machine]
        Audit[Immutable Audit Service]
    end

    subgraph External["External / AWS (Production)"]
        Bedrock[AWS Bedrock<br/>Claude 3.5 Sonnet + Titan]
        OS[OpenSearch Serverless]
        RDS[(PostgreSQL + pgvector)]
        S3[(S3 + KMS)]
    end

    UI --> Auth
    Auth --> Router
    Router --> MCP
    MCP --> RAG
    MCP --> LG
    LG --> DA
    DA --> MCP
    RAG --> MCP
    Memory --> MCP
    LG --> Review
    DA --> Memory
    Review --> Audit
    MCP --> Audit
    RAG -.-> OS
    RAG -.-> RDS
    LG -.-> Bedrock
    Memory -.-> RDS
    Audit -.-> S3
```

> **Key Principle**: No path to an LLM exists that bypasses the MCP Governance layer. Deep Agents and Memory are strictly governed.

---

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
careOS/
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

It is **not** a production deployment ready for real PHI without significant additional work (see [DEPLOYMENT.md](docs/DEPLOYMENT.md) and live AWS account + clinical validation).

See [GAP_CLOSURE_STATUS.md](docs/GAP_CLOSURE_STATUS.md) for the latest implementation-hardening status and remaining production work.
Enterprise hardening pass applied (CI security, middleware timeouts/size/tenant, PHI redaction logging, Docker non-root + secret files, config validation, frontend CSP/auth/client sanitization, DB pool, etc.). See PRODUCTION_UPGRADE_PLAN.md Phase 5.

**Deep technical guides:**
- [Deep Agents & Hindsight Memory Integration](docs/deep-agents-and-hindsight-memory.html) — Architecture + code-level explanation with interactive diagrams.
- [LinkedIn / Marketing Visual Deck](docs/careOS_LinkedIn.html) — Self-contained, beautiful single-file HTML with 4 production-accurate Mermaid block diagrams. Perfect for screenshots, carousels, or sharing the full visual story.

## License & Compliance Notice

For demonstration and educational use only. Any use with real patient data requires:
- Legal/compliance review
- Business Associate Agreements with AWS and any model providers
- Clinical safety validation
- Appropriate IRB/ethics oversight where applicable

---

**Built to the highest standards of clinical AI safety and healthcare compliance architecture.**
