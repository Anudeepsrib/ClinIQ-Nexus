import importlib.metadata as metadata

from services.agent_orchestration_service.app.deep_agents.deep_agent_factory import DeepAgentFactory


def test_official_deepagents_sdk_is_installed_and_factory_uses_it():
    assert metadata.version("deepagents") == "0.5.0"
    assert metadata.version("langchain") == "1.2.18"
    assert metadata.version("langgraph") == "1.1.10"

    agent = DeepAgentFactory.create(
        route="discharge_planning",
        tenant_id="tenant_hospital_a",
        hospital_id="hosp_001",
        facility_id=None,
        user_id="cc_001",
        role="care_coordinator",
        patient_id="pat_001",
        workflow_id="official_sdk_test",
    )

    assert agent is not None
    assert agent.langchain_deepagents_sdk_available is True
    assert agent.build_langchain_deep_agent("Governed discharge planning test prompt") is not None
