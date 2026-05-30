"""
Memory Classifier - Classifies memory candidates for sensitivity and type.
"""

from __future__ import annotations

from typing import Dict, Any


class MemoryClassifier:
    """
    Classifies proposed memories before governance.
    Determines sensitivity and whether it is safe for long-term storage.
    """

    def classify(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        content = candidate.get("content", "").lower()
        memory_type = candidate.get("memory_type", "preference")

        sensitivity = "low"
        if any(word in content for word in ["prefer", "always", "usually", "format", "summary"]):
            sensitivity = "low"
        elif any(word in content for word in ["patient", "family", "home"]):
            sensitivity = "medium"

        is_clinical = any(word in content for word in [
            "diagnosis", "lab", "medication", "dose", "vital", "abnormal", "critical"
        ])

        return {
            "memory_type": memory_type,
            "sensitivity_level": sensitivity,
            "is_clinical": is_clinical,
            "confidence": 0.9 if not is_clinical else 0.3,
        }
