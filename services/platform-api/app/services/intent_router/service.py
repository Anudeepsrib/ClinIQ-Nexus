"""
Intent Router Service - Deterministic-first classification.

This is one of the most important components in the entire platform.

Principles:
- Never use an agent or LLM as the primary router.
- Use fast, auditable, deterministic rules first.
- LLM (mock or real) only as fallback.
- Policy overrides for safety.
- Always log decision + reason.
"""

from __future__ import annotations

import re
from typing import List

from rapidfuzz import fuzz

from app.schemas.chat import RouteDecision
from app.core.config import settings

# Safety lexicon (expand in production)
SAFETY_KEYWORDS = {
    "chest_pain": ["chest pain", "chest pressure", "heart attack", "crushing chest"],
    "shortness_of_breath": ["can't breathe", "short of breath", "dyspnea", "suffocating"],
    "suicide_self_harm": ["kill myself", "suicide", "hurt myself", "end it all"],
    "severe_bleeding": ["bleeding heavily", "blood everywhere", "hemorrhaging"],
    "stroke_signs": ["face drooping", "arm weakness", "speech difficulty", "sudden numbness"],
}

EMERGENCY_OVERRIDE_ROUTES = {"clinical_safety_triage"}

ROLE_DEFAULTS = {
    "patient": "simple_rag",
    "clinician": "simple_rag",
    "nurse": "agentic_workflow",
    "care_coordinator": "discharge_planning",
    "admin": "hospital_operations",
}


async def route_intent(query: str, role: str, tenant_id: str) -> RouteDecision:
    """
    Hybrid intent classification with strong safety bias.
    """
    q = query.lower().strip()
    low_information_markers = {"asdf", "qwerty", "nonsense", "random", "gibberish"}

    # 1. Hard safety overrides (highest priority)
    for category, keywords in SAFETY_KEYWORDS.items():
        for kw in keywords:
            if kw in q:
                return RouteDecision(
                    intent="clinical_safety_triage",
                    confidence=0.99,
                    requires_agent=True,
                    requires_rag=True,
                    requires_human_review=True,
                    data_sources=["clinical_notes", "vitals", "nursing_notes"],
                    safety_flags=[f"emergency_{category}"],
                    reason=f"Safety keyword '{kw}' detected. Forcing clinical safety triage workflow.",
                )

    # 2. Strong deterministic rules
    if any(w in q for w in ["lab", "labs", "blood work", "results", "test results"]):
        return RouteDecision(
            intent="simple_rag",
            confidence=0.93,
            requires_rag=True,
            data_sources=["labs", "clinical_notes"],
            reason="User asked for lab or test result summary requiring grounded retrieval.",
        )

    if any(w in q for w in ["discharge", "going home", "ready to leave", "transport"]):
        return RouteDecision(
            intent="discharge_planning",
            confidence=0.89,
            requires_agent=True,
            requires_rag=True,
            requires_human_review=True,
            data_sources=["orders", "med_reconciliation", "appointments", "insurance"],
            safety_flags=["discharge_readiness"],
            reason="Discharge planning language detected. Requires agentic workflow + human review.",
        )

    if any(w in q for w in ["summarize", "summary", "last 72", "rounds", "chart"]):
        return RouteDecision(
            intent="simple_rag" if role in {"clinician", "nurse"} else "agentic_workflow",
            confidence=0.88,
            requires_rag=True,
            requires_agent=role == "nurse",
            data_sources=["clinical_notes", "vitals", "labs", "meds", "consults"],
            reason="Chart summarization request. Clinician gets direct RAG; nurse triggers risk agent.",
        )

    if any(w in q for w in ["prior auth", "insurance", "authorization", "coverage"]):
        return RouteDecision(
            intent="prior_authorization",
            confidence=0.91,
            requires_agent=True,
            requires_rag=True,
            requires_human_review=True,
            data_sources=["insurance_documents", "clinical_notes"],
            safety_flags=["billing_sensitive"],
            reason="Prior authorization / insurance document workflow requested.",
        )

    if any(w in q for w in ["message", "portal message", "patient wrote", "triage this"]):
        return RouteDecision(
            intent="patient_message_triage",
            confidence=0.87,
            requires_agent=True,
            data_sources=["patient_messages", "clinical_notes"],
            requires_human_review=True,
            reason="Patient message triage requested.",
        )

    if "what is" in q or "explain" in q or "how does" in q:
        return RouteDecision(
            intent="simple_llm",
            confidence=0.82,
            requires_rag=False,
            reason="General educational question. No PHI retrieval needed.",
        )

    # 3. Role-based default
    if any(marker in q for marker in low_information_markers):
        return RouteDecision(
            intent="simple_rag",
            confidence=0.55,
            requires_rag=True,
            requires_human_review=True,
            safety_flags=["low_confidence_fallback"],
            data_sources=["clinical_notes"],
            reason="Query was low-information or nonsensical. Defaulting to safer grounded retrieval with human review.",
        )

    # 4. Role-based default
    default_intent = ROLE_DEFAULTS.get(role, "simple_rag")

    # 5. LLM fallback (mocked for now - would call Bedrock Claude Haiku)
    # In production we would call the model router here with structured output
    llm_confidence = 0.71
    if llm_confidence > 0.65:
        return RouteDecision(
            intent=default_intent,
            confidence=llm_confidence,
            requires_rag=default_intent in {"simple_rag", "agentic_workflow"},
            requires_agent=default_intent in {"agentic_workflow", "discharge_planning"},
            data_sources=["clinical_notes"],
            reason="LLM fallback classification (mock). Defaulted based on role and query patterns.",
        )

    # 6. Ultimate safe fallback
    return RouteDecision(
        intent="simple_rag",
        confidence=0.55,
        requires_rag=True,
        requires_human_review=True,
        safety_flags=["low_confidence_fallback"],
        reason="Low confidence in classification. Defaulting to safest grounded retrieval path with human review.",
    )
