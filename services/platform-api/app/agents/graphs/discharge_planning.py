"""
Discharge Planning Agent — LangGraph implementation.

Demonstrates:
- Multi-step reasoning
- Tool use (scoped, governed)
- Human-in-the-loop gate via review queue
- Deep Agent style (planner + checker sub-flow)

This is the reference for all future agentic workflows in ClinIQ-Nexus.
"""

from __future__ import annotations

from typing import TypedDict, List, Optional, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.core.context import UserContext
from app.services.mcp.service import MCPContextGovernanceService
from app.api.v1.reviews import create_review_task
from app.providers.model_router import model_router

# Import the new mandatory Deep Agent layer
try:
    from services.agent_orchestration_service.app.deep_agents.deep_agent_factory import DeepAgentFactory
except ImportError:
    DeepAgentFactory = None  # Graceful fallback during incremental build


class DischargeState(TypedDict):
    patient_id: str
    user: UserContext
    query: str
    retrieved_context: List[Dict]
    plan: List[str]
    blockers: List[str]
    draft_summary: str
    requires_human_review: bool
    review_task_id: Optional[str]
    final_output: Optional[str]


async def retrieve_discharge_data(state: DischargeState) -> DischargeState:
    """Step 1: Gather governed data (orders, meds, notes, auth, transport, etc.)."""
    # In real system this would call multiple governed query tools
    # For demo we simulate high-quality retrieval
    state["retrieved_context"] = [
        {"doc_type": "discharge_summary", "content": "Primary: ADHF, improved. Meds reconciled. O2 2L pending auth."},
        {"doc_type": "progress_note", "content": "PT recommends home health. No falls. Family supportive."},
        {"doc_type": "insurance_prior_auth", "content": "Home O2 auth submitted but not yet approved."},
    ]
    return state


async def analyze_readiness(state: DischargeState) -> DischargeState:
    """Step 2: Identify blockers (this is where Deep Agent style planning shines)."""
    context = "\n".join(c["content"] for c in state["retrieved_context"])
    state["plan"] = [
        "Medication reconciliation complete",
        "Follow-up appointments scheduled",
        "Transportation arranged with daughter",
        "Home health nursing + PT ordered",
    ]
    state["blockers"] = []
    if "pending" in context.lower() or "auth" in context.lower():
        state["blockers"].append("Home oxygen prior authorization still pending")
    if "final PT" in context.lower():
        state["blockers"].append("Final PT clearance note not yet in chart")
    
    state["requires_human_review"] = len(state["blockers"]) > 0
    return state


async def draft_summary(state: DischargeState) -> DischargeState:
    """Step 3: Generate draft. For complex cases, delegate to Deep Agent."""
    mcp = MCPContextGovernanceService()
    mcp_dec = await mcp.govern(
        candidate_chunks=state["retrieved_context"],
        user=state["user"],
        route="discharge_planning",
        patient_id=state["patient_id"],
    )

    # === NEW: Mandatory Deep Agent integration for complex discharge planning ===
    if DeepAgentFactory:
        deep_agent = DeepAgentFactory.create(
            route="discharge_planning",
            tenant_id=state["user"].tenant_id,
            hospital_id=None,
            facility_id=None,
            user_id=state["user"].user_id,
            role=state["user"].role,
            patient_id=state["patient_id"],
            workflow_id="discharge_" + (state.get("patient_id") or "unknown"),
        )
        if deep_agent:
            deep_result = await deep_agent.run(state["query"], mcp_dec.allowed_context)
            state["draft_summary"] = deep_result.summary
            state["requires_human_review"] = deep_result.requires_human_review
            # Memory candidates from Deep Agent will be governed later
            return state
    # === End Deep Agent delegation ===

    gen = await model_router.generate(
        query=state["query"],
        allowed_context=mcp_dec.allowed_context,
        route="discharge_planning",
        user_role=state["user"].role,
        requires_review=state["requires_human_review"],
    )
    state["draft_summary"] = gen["text"]
    return state


async def human_review_gate(state: DischargeState) -> DischargeState:
    """Step 4: Create human review task if needed (hard gate)."""
    if state["requires_human_review"]:
        task = await create_review_task(
            task_type="discharge_readiness_review",
            patient_id=state["patient_id"],
            reason=" | ".join(state["blockers"]),
            assigned_to="care_coordinator",
            tenant_id=state["user"].tenant_id,
        )
        state["review_task_id"] = task["id"]
        state["final_output"] = (
            "DRAFT DISCHARGE READINESS SUMMARY CREATED.\n\n"
            f"{state['draft_summary']}\n\n"
            f"⚠️ BLOCKERS: {'; '.join(state['blockers'])}\n\n"
            f"This workflow is paused pending human review (Task: {task['id']})."
        )
    else:
        state["final_output"] = state["draft_summary"]
    return state


def build_discharge_graph():
    """Builds the LangGraph for discharge planning."""
    workflow = StateGraph(DischargeState)

    workflow.add_node("retrieve", retrieve_discharge_data)
    workflow.add_node("analyze", analyze_readiness)
    workflow.add_node("draft", draft_summary)
    workflow.add_node("gate", human_review_gate)

    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "analyze")
    workflow.add_edge("analyze", "draft")
    workflow.add_edge("draft", "gate")
    workflow.add_edge("gate", END)

    # MemorySaver gives us checkpointing / human-in-the-loop resumption
    return workflow.compile(checkpointer=MemorySaver())


discharge_graph = build_discharge_graph()
