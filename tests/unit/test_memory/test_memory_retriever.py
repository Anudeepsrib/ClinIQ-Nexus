import pytest

from services.memory_service.app.services.memory_retriever import MemoryRetriever


class FakeMemoryRepository:
    async def get_memories_for_user(self, tenant_id: str, user_id: str, limit: int = 10):
        return [
            {
                "id": "allowed",
                "tenant_id": tenant_id,
                "user_id": user_id,
                "role": "clinician",
                "patient_id": None,
                "memory_type": "formatting_preference",
                "memory_text_minimized": "Clinician prefers concise bullet summaries with citations first.",
                "sensitivity_level": "low",
            },
            {
                "id": "blocked_clinical",
                "tenant_id": tenant_id,
                "user_id": user_id,
                "role": "clinician",
                "patient_id": None,
                "memory_type": "clinical_note",
                "memory_text_minimized": "Patient diagnosis and medication dose details.",
                "sensitivity_level": "low",
            },
            {
                "id": "blocked_patient_scope",
                "tenant_id": tenant_id,
                "user_id": user_id,
                "role": "clinician",
                "patient_id": "other_patient",
                "memory_type": "workflow_preference",
                "memory_text_minimized": "Use short summaries.",
                "sensitivity_level": "low",
            },
            {
                "id": "blocked_sensitivity",
                "tenant_id": tenant_id,
                "user_id": user_id,
                "role": "clinician",
                "patient_id": None,
                "memory_type": "workflow_preference",
                "memory_text_minimized": "Use short summaries.",
                "sensitivity_level": "high",
            },
        ]


@pytest.mark.asyncio
async def test_memory_retriever_filters_to_governed_secondary_context():
    retriever = MemoryRetriever(FakeMemoryRepository())

    memories = await retriever.retrieve_for_context(
        tenant_id="tenant_hospital_a",
        user_id="doc_001",
        role="clinician",
        patient_id="pat_001",
        limit=5,
    )

    assert [memory["memory_id"] for memory in memories] == ["allowed"]
    assert memories[0]["sensitivity_level"] == "low"
