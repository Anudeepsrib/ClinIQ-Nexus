"""
careOS Canonical Use Case Demo Script

This script demonstrates all 7 core use cases from the original specification
using the real governed backend.

Run with a running docker compose environment.
"""

import asyncio
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()

DEMO_USERS = {
    "patient": "patient@hospital-a.demo",
    "clinician": "clinician@hospital-a.demo",
    "nurse": "nurse@hospital-a.demo",
    "care_coordinator": "care_coordinator@hospital-a.demo",
    "admin": "admin@hospital-a.demo",
}

QUERIES = {
    "patient_lab_summary": {
        "user": "patient",
        "query": "Can you summarize my recent lab results in simple language?",
        "patient_id": "pat_001",
        "expected_route": "simple_rag"
    },
    "patient_chest_pain": {
        "user": "patient",
        "query": "Should I be worried about my chest pain?",
        "patient_id": "pat_001",
        "expected_route": "clinical_safety_triage"
    },
    "clinician_72h": {
        "user": "clinician",
        "query": "Summarize this patient’s last 72 hours before rounds.",
        "patient_id": "pat_001",
        "expected_route": "simple_rag"
    },
    "nurse_risk": {
        "user": "nurse",
        "query": "Which patients on my floor may need follow-up based on overnight notes?",
        "patient_id": "pat_001",
        "use_workflow": "/workflows/risk-signal"
    },
    "care_coordinator_discharge": {
        "user": "care_coordinator",
        "query": "Create a discharge readiness summary for this patient.",
        "patient_id": "pat_001",
        "use_workflow": "/workflows/discharge-planning"
    },
    "admin_operations": {
        "user": "admin",
        "query": "What are the top reasons for delayed discharge this week?",
        "patient_id": None,
        "expected_route": "hospital_operations"
    },
    "general_education": {
        "user": "patient",
        "query": "What is an MRI?",
        "patient_id": None,
        "expected_route": "simple_llm"
    },
}


async def get_token(client: httpx.AsyncClient, email: str) -> str:
    resp = await client.post("/api/v1/auth/login", json={"email": email})
    return resp.json()["access_token"]


async def run_demo():
    console.print(Panel.fit("[bold cyan]careOS Canonical Use Case Demo[/bold cyan]"))
    console.print("This demonstrates the full governed architecture.\n")

    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=30.0) as client:
        for name, spec in QUERIES.items():
            console.rule(f"[bold]{name}[/bold]")
            email = DEMO_USERS[spec["user"]]
            token = await get_token(client, email)

            headers = {
                "Authorization": f"Bearer {token}",
                "X-Demo-User": email,
            }

            if spec.get("use_workflow"):
                # Agentic workflow
                resp = await client.post(
                    f"/api/v1{spec['use_workflow']}",
                    json={"patient_id": spec["patient_id"], "query": spec["query"]},
                    headers=headers,
                )
                data = resp.json()
                console.print(f"[green]Route/Workflow:[/green] {spec.get('use_workflow')}")
                console.print(f"[yellow]Risk Level / Status:[/yellow] {data.get('risk_level') or data.get('status')}")
                if "review_task_ids" in data and data["review_task_ids"]:
                    console.print("[red]Human Review Tasks Created[/red]")
            else:
                # Normal chat
                resp = await client.post(
                    "/api/v1/ai/chat",
                    json={"query": spec["query"], "patient_id": spec["patient_id"]},
                    headers=headers,
                )
                data = resp.json()
                console.print(f"[green]Route:[/green] {data['route']} (conf: {data['confidence']})")
                console.print(f"[blue]Requires Human Review:[/blue] {data['requires_human_review']}")
                if data.get("safety_flags"):
                    console.print(f"[red]Safety Flags:[/red] {data['safety_flags']}")

                # Show truncated response
                response_text = data["response"][:450] + "..." if len(data["response"]) > 450 else data["response"]
                console.print(Panel(Markdown(response_text), title="Response", border_style="dim"))

            console.print()

    console.print("[bold green]Demo complete.[/bold green] All queries passed through Intent Router + MCP Governance.")


if __name__ == "__main__":
    asyncio.run(run_demo())
