"""
Clinical Risk Signal Detection Agent (LangGraph)

Used heavily by nurses and care teams.

Detects possible deterioration signals from vitals, nursing notes, labs, missed meds, etc.
Returns structured risk assessment + forces human review on medium/high signals.
Never makes final clinical decisions.
"""

from __future__ import annotations

from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.core.context import UserContext
from app.services.mcp.service import MCPContextGovernanceService
from app.api.v1.reviews import create_review_task
from app.providers.model_router import model_router


class RiskState(TypedDict):
    patient_ids: List[str]          # Can analyze multiple patients (nurse floor view)
    user: UserContext
    query: str
    signals: List[Dict[str, Any]]   # Detected risk signals
    risk_level: str                 # low | medium | high
    summary: str
    requires_human_review: bool
    review_task_ids: List[str]


async def gather_overnight_data(state: RiskState) -> RiskState:
    """Gather recent notes, vitals, meds for the floor/patients."""
    # In real system: governed multi-patient query
    # For demo we seed strong signals
    state["signals"] = [
        {
            "patient_id": "pat_001",
            "type": "abnormal_vital",
            "description": "SpO2 dropped to 92% overnight (was 96%)",
            "severity": "medium",
            "source": "nursing_note",
        },
        {
            "patient_id": "pat_001",
            "type": "new_complaint",
            "description": "New leg swelling reported in patient message",
            "severity": "medium",
            "source": "patient_message",
        },
    ]
    return state


async def detect_risk_signals(state: RiskState) -> RiskState:
    """Run risk classification logic (in prod this can be a small model + rules)."""
    high_count = sum(1 for s in state["signals"] if s["severity"] == "high")
    med_count = sum(1 for s in state["signals"] if s["severity"] == "medium")

    if high_count > 0:
        state["risk_level"] = "high"
    elif med_count >= 2:
        state["risk_level"] = "medium"
    else:
        state["risk_level"] = "low"

    state["requires_human_review"] = state["risk_level"] in {"medium", "high"}
    return state


async def generate_structured_output(state: RiskState) -> RiskState:
    """Generate nurse-friendly structured summary and trigger review if needed."""
    mcp = MCPContextGovernanceService()
    signal_chunks = [
        {
            "tenant_id": state["user"].tenant_id,
            "patient_id": sig["patient_id"],
            "doc_type": "clinical_risk_signal",
            "sensitivity_level": "phi",
            "consent_scope": "treatment",
            "content": (
                f"{sig['type']} severity={sig['severity']}: "
                f"{sig['description']} source={sig['source']}"
            ),
        }
        for sig in state["signals"]
    ]
    # Governance still applies before detected clinical signals reach a model.
    mcp_dec = await mcp.govern(
        candidate_chunks=signal_chunks,
        user=state["user"],
        route="clinical_safety_triage",
        patient_id=None,
        query=state["query"],
    )
    state["requires_human_review"] = state["requires_human_review"] or mcp_dec.requires_human_review

    gen = await model_router.generate(
        query=state["query"],
        allowed_context=mcp_dec.allowed_context,
        route="clinical_safety_triage",
        user_role=state["user"].role,
        requires_review=state["requires_human_review"],
    )

    state["summary"] = gen["text"]

    if state["requires_human_review"]:
        for sig in state["signals"]:
            task = await create_review_task(
                task_type="clinical_risk_signal_review",
                patient_id=sig["patient_id"],
                reason=f"{sig['type']}: {sig['description']}",
                assigned_to="nurse",
                tenant_id=state["user"].tenant_id,
            )
            state["review_task_ids"].append(task["id"])

    return state


def build_risk_graph():
    workflow = StateGraph(RiskState)
    workflow.add_node("gather", gather_overnight_data)
    workflow.add_node("detect", detect_risk_signals)
    workflow.add_node("output", generate_structured_output)

    workflow.set_entry_point("gather")
    workflow.add_edge("gather", "detect")
    workflow.add_edge("detect", "output")
    workflow.add_edge("output", END)

    return workflow.compile(checkpointer=MemorySaver())


risk_signal_graph = build_risk_graph()
