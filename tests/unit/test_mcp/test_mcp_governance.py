"""
Critical tests for the MCP Context Governance Service.

These tests prove that PHI cannot leak outside authorized scope.
"""

import pytest
import asyncio

from app.services.mcp.service import MCPContextGovernanceService
from app.core.context import UserContext


@pytest.mark.asyncio
async def test_mcp_blocks_cross_tenant_access():
    mcp = MCPContextGovernanceService()
    user = UserContext(
        user_id="doc_001", role="clinician", tenant_id="tenant_hospital_a",
        email="doc@test.com", full_name="Dr Test",
        can_access_all_patients_in_tenant=True
    )

    chunks = [
        {"tenant_id": "tenant_hospital_b", "patient_id": "pat_x", "content": "Secret data", "doc_type": "note", "sensitivity_level": "phi", "consent_scope": "treatment"},
        {"tenant_id": "tenant_hospital_a", "patient_id": "pat_001", "content": "Allowed data", "doc_type": "note", "sensitivity_level": "phi", "consent_scope": "treatment"},
    ]

    decision = await mcp.govern(chunks, user, "simple_rag", "pat_001")
    assert decision.blocked_context_count >= 1
    assert len(decision.allowed_context) == 1
    assert "tenant_mismatch_blocked" in decision.policy_decisions


@pytest.mark.asyncio
async def test_mcp_flags_abnormal_values_for_patient_facing():
    mcp = MCPContextGovernanceService()
    patient = UserContext(
        user_id="pat_001", role="patient", tenant_id="tenant_hospital_a",
        email="patient@test.com", full_name="Maria",
        assigned_patient_ids={"pat_001"}
    )

    chunks = [
        {"tenant_id": "tenant_hospital_a", "patient_id": "pat_001", "content": "Glucose critical high 450 mg/dL", "doc_type": "lab", "sensitivity_level": "phi", "consent_scope": "treatment"},
    ]

    decision = await mcp.govern(chunks, patient, "simple_rag", "pat_001")
    assert decision.requires_human_review is True
    assert any("abnormal" in p for p in decision.policy_decisions)


@pytest.mark.asyncio
async def test_mcp_role_transformation_for_admin():
    mcp = MCPContextGovernanceService()
    admin = UserContext(
        user_id="admin_001", role="admin", tenant_id="tenant_hospital_a",
        email="admin@test.com", full_name="Admin",
    )

    chunks = [
        {"tenant_id": "tenant_hospital_a", "patient_id": "pat_001", "content": "Detailed clinical note with diagnosis", "doc_type": "note", "sensitivity_level": "phi", "consent_scope": "treatment"},
    ]

    decision = await mcp.govern(chunks, admin, "hospital_operations", None)
    # Admins should get heavily transformed/de-identified content
    assert "De-identified" in decision.allowed_context[0]["content"] or len(decision.allowed_context) == 0
