from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid

from app.core.context import get_current_user, get_current_tenant
from app.agents.graphs.discharge_planning import discharge_graph

# Mandatory Deep Agent layer (per architecture spec)
try:
    from services.agent_orchestration_service.app.deep_agents.deep_agent_factory import DeepAgentFactory
    from app.services.mcp.service import MCPContextGovernanceService
    DEEP_AGENTS_AVAILABLE = True
except Exception:
    DeepAgentFactory = None
    MCPContextGovernanceService = None
    DEEP_AGENTS_AVAILABLE = False

router = APIRouter()


class WorkflowRequest(BaseModel):
    patient_id: str
    query: str


@router.post("/discharge-planning")
async def discharge_planning(req: WorkflowRequest, user=Depends(get_current_user)):
    """
    Real LangGraph discharge planning workflow.
    Demonstrates planning, data gathering, blocker detection, and hard human review gate.
    """
    initial_state = {
        "patient_id": req.patient_id,
        "user": user,
        "query": req.query,
        "retrieved_context": [],
        "plan": [],
        "blockers": [],
        "draft_summary": "",
        "requires_human_review": False,
        "review_task_id": None,
        "final_output": None,
    }

    # Run the graph (this is a real multi-step agentic workflow)
    config = {"configurable": {"thread_id": f"discharge_{req.patient_id}"}}
    result = await discharge_graph.ainvoke(initial_state, config=config)

    return {
        "workflow": "discharge_planning",
        "status": "completed" if not result.get("requires_human_review") else "awaiting_human_review",
        "output": result.get("final_output"),
        "blockers": result.get("blockers", []),
        "review_task_id": result.get("review_task_id"),
        "requires_human_review": result.get("requires_human_review", False),
    }


from app.agents.graphs.clinical_risk_signal import risk_signal_graph
from app.agents.graphs.chart_summary import chart_summary_graph


@router.post("/chart-summary")
async def chart_summary(req: WorkflowRequest, user=Depends(get_current_user)):
    """
    Real 72-hour Clinician Chart Summary.
    For complex multi-source cases, delegates to ClinicalChartDeepAgent (mandatory Deep Agent pattern).
    """
    # First run LangGraph to gather governed context
    initial_state: Dict[str, Any] = {
        "patient_id": req.patient_id,
        "user": user,
        "query": req.query,
        "raw_chunks": [],
        "governed_context": [],
        "summary": "",
        "unresolved_issues": [],
        "citations": [],
        "requires_human_review": False,
        "review_task_id": None,
    }

    config = {"configurable": {"thread_id": f"chart_{req.patient_id}"}}
    langgraph_result = await chart_summary_graph.ainvoke(initial_state, config=config)

    # Deep Agent delegation for complex cases (as per spec)
    if DEEP_AGENTS_AVAILABLE and len(langgraph_result.get("governed_context", [])) > 3:
        deep_agent = DeepAgentFactory.create(
            route="chart_summary_complex",
            tenant_id=user.tenant_id,
            hospital_id=None,
            facility_id=None,
            user_id=user.user_id,
            role=user.role,
            patient_id=req.patient_id,
            workflow_id=f"chart_deep_{req.patient_id}",
        )
        if deep_agent:
            # Apply MCP one more time before handing to Deep Agent (defense in depth)
            mcp = MCPContextGovernanceService()
            mcp_decision = await mcp.govern(
                candidate_chunks=langgraph_result.get("governed_context", []),
                user=user,
                route="chart_summary_complex",
                patient_id=req.patient_id,
            )
            deep_result = await deep_agent.run(req.query, mcp_decision.allowed_context)
            return {
                "workflow": "clinician_72h_chart_summary_deep_agent",
                "summary": deep_result.summary,
                "findings": deep_result.findings,
                "requires_human_review": deep_result.requires_human_review,
                "human_review_reason": deep_result.human_review_reason,
                "memory_candidates": deep_result.memory_candidates,
                "sub_agent_steps": deep_result.sub_agent_steps,
            }

    # Fallback to pure LangGraph result
    return {
        "workflow": "clinician_72h_chart_summary",
        "summary": langgraph_result.get("summary"),
        "unresolved_issues": langgraph_result.get("unresolved_issues", []),
        "citations": langgraph_result.get("citations", []),
        "requires_human_review": langgraph_result.get("requires_human_review"),
        "review_task_id": langgraph_result.get("review_task_id"),
    }


@router.post("/risk-signal")
async def risk_signal_detection(req: WorkflowRequest, user=Depends(get_current_user)):
    """
    Real Clinical Risk Signal Detection Agent (nurse floor use case).
    """
    initial_state: Dict[str, Any] = {
        "patient_ids": [req.patient_id] if req.patient_id else ["pat_001"],
        "user": user,
        "query": req.query,
        "signals": [],
        "risk_level": "low",
        "summary": "",
        "requires_human_review": False,
        "review_task_ids": [],
    }

    config = {"configurable": {"thread_id": f"risk_{req.patient_id or 'floor'}"}}
    result = await risk_signal_graph.ainvoke(initial_state, config=config)

    return {
        "workflow": "clinical_risk_signal",
        "risk_level": result.get("risk_level"),
        "signals": result.get("signals"),
        "summary": result.get("summary"),
        "requires_human_review": result.get("requires_human_review"),
        "review_task_ids": result.get("review_task_ids", []),
    }


# ============================================================
# NEW: Complex workflows wired to mandatory Deep Agents
# ============================================================

@router.post("/prior-authorization")
async def prior_authorization(req: WorkflowRequest, user=Depends(get_current_user)):
    """
    Prior Authorization workflow using PriorAuthorizationDeepAgent.
    This is a mandatory Deep Agent use case per the platform architecture.
    """
    if not DEEP_AGENTS_AVAILABLE:
        return {"error": "Deep Agents not available in this environment", "status": "degraded"}

    # Gather governed context first (via RAG service or LangGraph if available)
    # For demo we pass empty and let the Deep Agent use its scoped tools
    mcp = MCPContextGovernanceService()
    mcp_decision = await mcp.govern(
        candidate_chunks=[],
        user=user,
        route="prior_authorization",
        patient_id=req.patient_id,
    )

    deep_agent = DeepAgentFactory.create(
        route="prior_authorization",
        tenant_id=user.tenant_id,
        hospital_id=None,
        facility_id=None,
        user_id=user.user_id,
        role=user.role,
        patient_id=req.patient_id,
        workflow_id=f"prior_auth_{req.patient_id}",
    )

    if not deep_agent:
        return {"error": "No Deep Agent registered for this route"}

    deep_result = await deep_agent.run(req.query, mcp_decision.allowed_context)

    return {
        "workflow": "prior_authorization_deep_agent",
        "summary": deep_result.summary,
        "findings": deep_result.findings,
        "requires_human_review": deep_result.requires_human_review,
        "human_review_reason": deep_result.human_review_reason,
        "memory_candidates": deep_result.memory_candidates,
        "sub_agent_steps": deep_result.sub_agent_steps,
    }


@router.post("/message-triage")
async def patient_message_triage(req: WorkflowRequest, user=Depends(get_current_user)):
    """
    Patient Message Triage using PatientMessageTriageDeepAgent.
    """
    if not DEEP_AGENTS_AVAILABLE:
        return {"error": "Deep Agents not available", "status": "degraded"}

    mcp = MCPContextGovernanceService()
    mcp_decision = await mcp.govern(
        candidate_chunks=[],
        user=user,
        route="patient_message_triage",
        patient_id=req.patient_id,
    )

    deep_agent = DeepAgentFactory.create(
        route="patient_message_triage",
        tenant_id=user.tenant_id,
        hospital_id=None,
        facility_id=None,
        user_id=user.user_id,
        role=user.role,
        patient_id=req.patient_id,
        workflow_id=f"message_triage_{req.patient_id}",
    )

    if not deep_agent:
        return {"error": "No Deep Agent for message triage"}

    deep_result = await deep_agent.run(req.query, mcp_decision.allowed_context)

    return {
        "workflow": "patient_message_triage_deep_agent",
        "summary": deep_result.summary,
        "findings": deep_result.findings,
        "requires_human_review": deep_result.requires_human_review,
        "safety_flags": deep_result.safety_flags,
        "memory_candidates": deep_result.memory_candidates,
    }


@router.post("/compliance-review")
async def compliance_review(req: WorkflowRequest, user=Depends(get_current_user)):
    """
    Compliance investigation workflow using ComplianceReviewDeepAgent.
    """
    if not DEEP_AGENTS_AVAILABLE:
        return {"error": "Deep Agents not available", "status": "degraded"}

    mcp = MCPContextGovernanceService()
    mcp_decision = await mcp.govern(
        candidate_chunks=[],
        user=user,
        route="compliance_review",
        patient_id=req.patient_id,
    )

    deep_agent = DeepAgentFactory.create(
        route="compliance_review",
        tenant_id=user.tenant_id,
        hospital_id=None,
        facility_id=None,
        user_id=user.user_id,
        role=user.role,
        patient_id=req.patient_id,
        workflow_id=f"compliance_{req.patient_id}",
    )

    if not deep_agent:
        return {"error": "No Deep Agent for compliance review"}

    deep_result = await deep_agent.run(req.query, mcp_decision.allowed_context)

    return {
        "workflow": "compliance_review_deep_agent",
        "summary": deep_result.summary,
        "findings": deep_result.findings,
        "requires_human_review": deep_result.requires_human_review,
        "safety_flags": deep_result.safety_flags,
    }
