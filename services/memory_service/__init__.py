"""Import shim for ``services/memory-service``."""

from __future__ import annotations

from pathlib import Path

_real_package = Path(__file__).resolve().parents[1] / "memory-service"
__path__ = [str(_real_package)]

