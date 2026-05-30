"""
Critical tests for the Deterministic-First Intent Router.

These tests are non-negotiable for safety.
"""

import pytest
import asyncio

from app.services.intent_router.service import route_intent


@pytest.mark.asyncio
async def test_emergency_chest_pain_forces_safety_triage():
    decision = await route_intent("I have terrible chest pain and feel dizzy", "patient", "tenant_hospital_a")
    assert decision.intent == "clinical_safety_triage"
    assert decision.requires_human_review is True
    assert "emergency" in str(decision.safety_flags) or decision.confidence > 0.95


@pytest.mark.asyncio
async def test_lab_summary_routes_to_simple_rag():
    decision = await route_intent("Can you explain my recent blood work results?", "patient", "tenant_hospital_a")
    assert decision.intent == "simple_rag"
    assert decision.requires_rag is True


@pytest.mark.asyncio
async def test_discharge_planning_routes_correctly():
    decision = await route_intent("Is my mom ready to go home? We need the discharge summary.", "care_coordinator", "tenant_hospital_a")
    assert decision.intent == "discharge_planning"
    assert decision.requires_human_review is True


@pytest.mark.asyncio
async def test_general_question_routes_to_simple_llm():
    decision = await route_intent("What is an echocardiogram?", "patient", "tenant_hospital_a")
    assert decision.intent == "simple_llm"
    assert decision.requires_rag is False


@pytest.mark.asyncio
async def test_low_confidence_still_defaults_safe():
    decision = await route_intent("asdfghjkl random nonsense query", "admin", "tenant_hospital_a")
    # Must never explode — should default to safest path
    assert decision.intent in {"simple_rag", "simple_llm"}
    assert decision.confidence < 0.7
