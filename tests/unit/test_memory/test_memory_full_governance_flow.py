"""
Comprehensive tests for the full Hindsight Memory governance pipeline.

These tests verify that clinical content is blocked, only safe memories are stored,
and the complete Extract → Classify → Govern → Write → Audit flow works correctly.
"""

import pytest
from services.memory_service.app.services.hindsight_memory_service import HindsightMemoryService


@pytest.mark.asyncio
async def test_memory_blocks_clinical_content():
    service = HindsightMemoryService()

    dangerous_candidate = {
        "content": "Patient has elevated troponin and new atrial fibrillation.",
        "memory_type": "clinical_note",
        "patient_id": "pat_001",
    }

    result = await service.process_memory_candidate(
        candidate=dangerous_candidate,
        user_role="clinician",
        tenant_id="tenant_hospital_a",
        user_id="doc_001",
    )

    assert result["status"] == "blocked"
    assert "clinical" in result.get("reason", "").lower() or "forbidden" in result.get("reason", "").lower()


@pytest.mark.asyncio
async def test_memory_approves_safe_workflow_preference():
    service = HindsightMemoryService()

    safe_candidate = {
        "content": "Care coordinator prefers to see transportation barriers and insurance authorization status first in every discharge summary.",
        "memory_type": "workflow_preference",
        "source_workflow_id": "discharge_123",
    }

    result = await service.process_memory_candidate(
        candidate=safe_candidate,
        user_role="care_coordinator",
        tenant_id="tenant_hospital_a",
        user_id="cc_001",
    )

    assert result["status"] == "stored"
    assert "memory_id" in result


@pytest.mark.asyncio
async def test_memory_retrieval_respects_role_and_tenant():
    service = HindsightMemoryService()

    # This should return only safe, pre-approved memories for the context
    memories = await service.retrieve_governed_memories(
        tenant_id="tenant_hospital_a",
        user_id="clinician_001",
        role="clinician",
        patient_id="pat_001",
    )

    # In the current seeded environment we expect either empty or only low-sensitivity preferences
    for mem in memories:
        assert "diagnosis" not in mem.get("memory_text_minimized", "").lower()
        assert "lab" not in mem.get("memory_text_minimized", "").lower()
        assert mem.get("sensitivity_level") in ["low", "medium"]


@pytest.mark.asyncio
async def test_memory_proposal_from_deep_agent_is_governed():
    """
    Simulates a Deep Agent proposing a memory.
    The proposal must still go through full governance.
    """
    service = HindsightMemoryService()

    agent_proposal = {
        "content": "Clinician prefers bullet-point summaries with citations listed at the top.",
        "memory_type": "formatting_preference",
        "source_workflow_id": "chart_summary_deep_001",
    }

    result = await service.process_memory_candidate(
        candidate=agent_proposal,
        user_role="clinician",
        tenant_id="tenant_hospital_a",
        user_id="doc_001",
    )

    # This one should be approved
    assert result["status"] in ["stored", "approved"]
