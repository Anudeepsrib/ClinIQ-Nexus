import pytest

from services.memory_service.app.services.memory_audit import MEMORY_AUDIT_EVENTS, MemoryAuditService


@pytest.mark.asyncio
async def test_memory_audit_does_not_store_raw_candidate_content():
    MEMORY_AUDIT_EVENTS.clear()
    audit = MemoryAuditService()

    await audit.log_memory_decision(
        tenant_id="tenant_hospital_a",
        user_id="doc_001",
        decision="blocked",
        candidate_content="Patient has elevated troponin.",
        minimized_content=None,
        reason="Contains forbidden clinical content",
        policy_tags=["memory_blocked_clinical_content"],
    )

    event = MEMORY_AUDIT_EVENTS[0]
    assert "candidate_content" not in event
    assert event["candidate_hash"]
    assert event["candidate_length"] == len("Patient has elevated troponin.")
