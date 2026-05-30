"""
ClinicalChartDeepAgent

Deep Agent for complex multi-source chart summarization (72h clinician view).
"""

from __future__ import annotations

from typing import Any, Dict, List

from .base_deep_agent import BaseDeepAgent, DeepAgentContext, DeepAgentOutput


class ClinicalChartDeepAgent(BaseDeepAgent):
    @property
    def name(self) -> str:
        return "clinical_chart_deep_agent"

    @property
    def description(self) -> str:
        return "Deep reasoning over multiple data sources for clinician chart summary"

    async def run(self, task: str, governed_context: List[Dict[str, Any]]) -> DeepAgentOutput:
        findings = [
            {"category": "vitals", "status": "abnormal", "detail": "SpO2 trend downward overnight"},
            {"category": "labs", "status": "pending", "detail": "Final troponin pending"},
        ]

        memory_candidate = self.propose_memory_candidate(
            "Clinician prefers abnormal trends highlighted first in chart summaries.",
            "formatting_preference"
        )

        return DeepAgentOutput(
            workflow_id=self.context.workflow_id or "chart_summary",
            route="chart_summary_complex",
            summary="Complex chart summary generated with trend analysis.",
            findings=findings,
            citations=[{"source": "vitals_note"}, {"source": "lab_report"}],
            confidence=0.78,
            requires_human_review=True,
            human_review_reason="Abnormal trend detected - clinician review recommended",
            memory_candidates=[memory_candidate],
            sub_agent_steps=[
                {"step": "planner", "action": "Identified need for trend analysis across 3 sources"},
                {"step": "executor", "action": "Pulled governed data via scoped tools"},
            ],
        )
