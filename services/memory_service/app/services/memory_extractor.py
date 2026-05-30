"""
Memory Extractor - Identifies durable, non-clinical facts worth remembering.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class MemoryExtractor:
    """
    Extracts potential memory candidates from agent outputs or chat turns.
    Very conservative by design.
    """

    def extract_candidates(self, text: str, role: str, source: str = "chat") -> List[Dict[str, Any]]:
        candidates: List[Dict[str, Any]] = []

        lowered = text.lower()

        if "prefer" in lowered or "always" in lowered or "usually" in lowered:
            if "bullet" in lowered or "summary" in lowered or "format" in lowered:
                candidates.append({
                    "content": text.strip(),
                    "memory_type": "formatting_preference",
                    "source": source,
                })

            if "discharge" in lowered and ("blocker" in lowered or "transport" in lowered):
                candidates.append({
                    "content": text.strip(),
                    "memory_type": "workflow_preference",
                    "source": source,
                })

        return candidates
