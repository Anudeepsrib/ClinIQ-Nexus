"""
Critical tests for Deep Agent tool scoping and least-privilege enforcement.

These tests verify that the DeepAgentFactory only grants appropriate tools
based on route and role — a core production safety requirement.
"""

import pytest
from services.agent_orchestration_service.app.deep_agents.deep_agent_factory import DeepAgentFactory
from services.agent_orchestration_service.app.deep_agents.base_deep_agent import DeepAgentContext


def _make_context(role: str = "clinician", route: str = "discharge_planning") -> DeepAgentContext:
    return DeepAgentContext(
        tenant_id="tenant_hospital_a",
        hospital_id="hosp_001",
        facility_id=None,
        user_id="user_001",
        role=role,
        patient_id="pat_001",
        workflow_id=f"test_{route}",
        permissions=[],
    )


def test_discharge_planning_agent_gets_document_and_memory_tools():
    ctx = _make_context(role="care_coordinator", route="discharge_planning")
    agent = DeepAgentFactory.create(
        route="discharge_planning",
        tenant_id=ctx.tenant_id,
        hospital_id=ctx.hospital_id,
        facility_id=None,
        user_id=ctx.user_id,
        role=ctx.role,
        patient_id=ctx.patient_id,
        workflow_id=ctx.workflow_id,
    )

    tool_names = [t.name for t in agent.allowed_tools]

    assert "get_document_metadata" in tool_names
    assert "retrieve_governed_memory" in tool_names
    assert "propose_memory_candidate" in tool_names
    assert "create_human_review_task" in tool_names
    assert "governed_rag_search" in tool_names


def test_compliance_agent_does_not_get_patient_clinical_tools():
    ctx = _make_context(role="compliance_officer", route="compliance_review")
    agent = DeepAgentFactory.create(
        route="compliance_review",
        tenant_id=ctx.tenant_id,
        hospital_id=ctx.hospital_id,
        facility_id=None,
        user_id=ctx.user_id,
        role=ctx.role,
        patient_id=None,
        workflow_id=ctx.workflow_id,
    )

    tool_names = [t.name for t in agent.allowed_tools]

    # Compliance should have very limited tools
    assert "get_document_metadata" not in tool_names
    assert "retrieve_governed_memory" not in tool_names  # No patient memory access
    assert "log_deep_agent_decision" in tool_names  # Should have audit logging


def test_nurse_gets_memory_but_not_prior_auth_document_tools():
    ctx = _make_context(role="nurse", route="patient_message_triage")
    agent = DeepAgentFactory.create(
        route="patient_message_triage",
        tenant_id=ctx.tenant_id,
        hospital_id=ctx.hospital_id,
        facility_id=None,
        user_id=ctx.user_id,
        role=ctx.role,
        patient_id=ctx.patient_id,
        workflow_id=ctx.workflow_id,
    )

    tool_names = [t.name for t in agent.allowed_tools]

    assert "retrieve_governed_memory" in tool_names
    assert "get_document_metadata" not in tool_names  # Nurses shouldn't pull insurance docs directly


def test_factory_returns_none_for_non_deep_agent_routes():
    agent = DeepAgentFactory.create(
        route="simple_rag",  # Should never get a Deep Agent
        tenant_id="tenant_hospital_a",
        hospital_id=None,
        facility_id=None,
        user_id="user_001",
        role="patient",
        patient_id="pat_001",
    )

    assert agent is None
