"""
72-Hour Clinician Chart Summary Agent (LangGraph)

Core clinician use case:
- Retrieves recent notes, vitals, labs, meds, imaging summaries, nursing notes, consults
- Produces concise, rounds-ready summary with citations
- Highlights unresolved issues
- Never invents missing information
- Requires citations + human review on any medium risk signals
"""

from __future__ import annotations

from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.core.context import UserContext
from app.services.rag.service import retrieve_authorized_chunks
from app.services.mcp.service import MCPContextGovernanceService
from app.providers.model_router import model_router

# Deep Agent support (mandatory architecture)
try:
    from services.agent_orchestration_service.app.deep_agents.deep_agent_factory import DeepAgentFactory
except ImportError:
    DeepAgentFactory = None
from app.api.v1.reviews import create_review_task


class ChartSummaryState(TypedDict):
    patient_id: str
    user: UserContext
    query: str
    raw_chunks: List[Dict]
    governed_context: List[Dict]
    summary: str
    unresolved_issues: List[str]
    citations: List[Dict]
    requires_human_review: bool
    review_task_id: Optional[str]


async def retrieve_recent_data(state: ChartSummaryState) -> ChartSummaryState:
    """Step 1: Pull last 72h authorized data across multiple document types."""
    chunks = await retrieve_authorized_chunks(
        query="last 72 hours vitals labs notes medications consults imaging nursing",
        user=state["user"],
        patient_id=state["patient_id"],
        top_k=12,
    )
    state["raw_chunks"] = chunks
    return state


async def govern_and_filter(state: ChartSummaryState) -> ChartSummaryState:
    """Step 2: Mandatory MCP governance."""
    mcp = MCPContextGovernanceService()
    decision = await mcp.govern(
        candidate_chunks=state["raw_chunks"],
        user=state["user"],
        route="simple_rag",
        patient_id=state["patient_id"],
        query=state["query"],
    )
    state["governed_context"] = decision.allowed_context
    state["requires_human_review"] = decision.requires_human_review
    return state


async def synthesize_summary(state: ChartSummaryState) -> ChartSummaryState:
    """Step 3: Generate summary. For complex cases delegate to ClinicalChartDeepAgent."""
    # Deep Agent delegation for complex multi-source chart work
    if DeepAgentFactory and len(state.get("governed_context", [])) > 4:
        deep_agent = DeepAgentFactory.create(
            route="chart_summary_complex",
            tenant_id=state["user"].tenant_id,
            hospital_id=None,
            facility_id=None,
            user_id=state["user"].user_id,
            role=state["user"].role,
            patient_id=state["patient_id"],
            workflow_id="chart_deep_" + (state.get("patient_id") or "unknown"),
        )
        if deep_agent:
            deep_result = await deep_agent.run(state["query"], state.get("governed_context", []))
            state["summary"] = deep_result.summary
            state["unresolved_issues"] = [f.get("detail") for f in deep_result.findings if f.get("status") in ("blocker", "pending")]
            state["citations"] = deep_result.citations
            state["requires_human_review"] = deep_result.requires_human_review
            return state

    # Standard path
    gen = await model_router.generate(
        query=state["query"],
        allowed_context=state["governed_context"],
        route="simple_rag",
        user_role=state["user"].role,
        requires_review=state["requires_human_review"],
    )

    state["summary"] = gen["text"]

    # Simple heuristic for unresolved issues (in prod this would be more sophisticated)
    context_blob = " ".join(c.get("content", "") for c in state["governed_context"]).lower()
    issues = []
    if "pending" in context_blob:
        issues.append("Pending results or orders noted")
    if "follow up" in context_blob or "follow-up" in context_blob:
        issues.append("Follow-up actions mentioned but not confirmed complete")
    if "abnormal" in context_blob or "critical" in context_blob:
        issues.append("Abnormal/critical values present — review source data")

    state["unresolved_issues"] = issues

    # Build citations
    state["citations"] = [
        {
            "document_id": c.get("document_id"),
            "doc_type": c.get("doc_type"),
            "snippet": c.get("content", "")[:220] + "...",
        }
        for c in state["governed_context"][:5]
    ]

    return state


async def final_gate(state: ChartSummaryState) -> ChartSummaryState:
    """Step 4: Apply human review gate if needed."""
    if state["requires_human_review"] or state["unresolved_issues"]:
        task = create_review_task(
            task_type="clinician_chart_summary_review",
            patient_id=state["patient_id"],
            reason="Chart summary generated with unresolved issues or risk signals",
            assigned_to="clinician",
        )
        state["review_task_id"] = task["id"]
        state["requires_human_review"] = True
    return state


def build_chart_summary_graph():
    workflow = StateGraph(ChartSummaryState)

    workflow.add_node("retrieve", retrieve_recent_data)
    workflow.add_node("govern", govern_and_filter)
    workflow.add_node("synthesize", synthesize_summary)
    workflow.add_node("gate", final_gate)

    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "govern")
    workflow.add_edge("govern", "synthesize")
    workflow.add_edge("synthesize", "gate")
    workflow.add_edge("gate", END)

    return workflow.compile(checkpointer=MemorySaver())


chart_summary_graph = build_chart_summary_graph()
