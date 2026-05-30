"""Import shim for ``services/agent-orchestration-service``."""

from __future__ import annotations

from pathlib import Path

_real_package = Path(__file__).resolve().parents[1] / "agent-orchestration-service"
__path__ = [str(_real_package)]

