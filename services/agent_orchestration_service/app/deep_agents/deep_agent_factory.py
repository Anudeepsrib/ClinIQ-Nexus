"""
DeepAgentFactory - The single entry point for creating governed Deep Agents.

This factory is the enforcement point for:
- Route-specific Deep Agent allowlisting
- Tenant + role isolation
- Tool scoping per agent type
- Permission checks
"""

from __future__ import annotations

from typing import Dict, List, Optional, Type

from .base_deep_agent import BaseDeepAgent, DeepAgentContext
from .discharge_planning_deep_agent import DischargePlanningDeepAgent
from .clinical_chart_deep_agent import ClinicalChartDeepAgent
from .patient_message_triage_deep_agent import PatientMessageTriageDeepAgent
from .prior_authorization_deep_agent import PriorAuthorizationDeepAgent
from .hospital_operations_deep_agent import HospitalOperationsDeepAgent
from .compliance_review_deep_agent import ComplianceReviewDeepAgent

# Route → Deep Agent mapping (only complex routes get Deep Agents)
DEEP_AGENT_REGISTRY: Dict[str, Type[BaseDeepAgent]] = {
    "discharge_planning": DischargePlanningDeepAgent,
    "chart_summary_complex": ClinicalChartDeepAgent,
    "patient_message_triage": PatientMessageTriageDeepAgent,
    "prior_authorization": PriorAuthorizationDeepAgent,
    "hospital_operations": HospitalOperationsDeepAgent,
    "compliance_review": ComplianceReviewDeepAgent,
}


class DeepAgentFactory:
    """
    Factory that creates properly scoped and governed Deep Agents.
    """

    @staticmethod
    def create(
        route: str,
        tenant_id: str,
        hospital_id: Optional[str],
        facility_id: Optional[str],
        user_id: str,
        role: str,
        patient_id: Optional[str] = None,
        encounter_id: Optional[str] = None,
        permissions: Optional[List[str]] = None,
        workflow_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Optional[BaseDeepAgent]:
        """
        Create a Deep Agent for a given route.

        Returns None if the route does not require a Deep Agent.
        """
        agent_class = DEEP_AGENT_REGISTRY.get(route)
        if not agent_class:
            return None  # This route does not use Deep Agents

        context = DeepAgentContext(
            tenant_id=tenant_id,
            hospital_id=hospital_id,
            facility_id=facility_id,
            user_id=user_id,
            role=role,
            patient_id=patient_id,
            encounter_id=encounter_id,
            permissions=permissions or [],
            workflow_id=workflow_id,
            correlation_id=correlation_id,
        )

        agent = agent_class(context)

        # Factory-level enforcement of scoped tools
        DeepAgentFactory._register_scoped_tools(agent, route, role)

        return agent

    @staticmethod
    def _register_scoped_tools(agent: BaseDeepAgent, route: str, role: str) -> None:
        """
        Register only the tools this specific Deep Agent + role combination is allowed to use.
        This is a critical security boundary.
        """
        from .tools.rag_tools import GovernedRAGTool
        from .tools.memory_tools import (
            AuditMemoryEventTool,
            ClassifyMemoryCandidateTool,
            RetrieveGovernedMemoryTool,
            ProposeMemoryCandidateTool,
        )
        from .tools.human_review_tools import CreateHumanReviewTaskTool
        from .tools.document_tools import GetDocumentMetadataTool
        from .tools.audit_tools import LogDeepAgentDecisionTool

        # Base tools almost all Deep Agents get (but still governed)
        agent.register_tool(GovernedRAGTool(agent.context))
        agent.register_tool(ProposeMemoryCandidateTool(agent.context))
        agent.register_tool(ClassifyMemoryCandidateTool(agent.context))
        agent.register_tool(AuditMemoryEventTool(agent.context))
        agent.register_tool(CreateHumanReviewTaskTool(agent.context))

        # Route-specific tools
        if route in ["discharge_planning", "prior_authorization"]:
            agent.register_tool(GetDocumentMetadataTool(agent.context))

        if route in ["chart_summary_complex", "hospital_operations"]:
            agent.register_tool(GovernedRAGTool(agent.context))

        if role in ["clinician", "care_coordinator", "nurse"]:
            agent.register_tool(RetrieveGovernedMemoryTool(agent.context))

        # Compliance and operations agents get audit logging capability
        if role == "compliance_officer" or route in ["compliance_review", "hospital_operations"]:
            agent.register_tool(LogDeepAgentDecisionTool(agent.context))
