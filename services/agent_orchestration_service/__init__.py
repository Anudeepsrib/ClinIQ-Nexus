"""Import shim for the Deep Agent service package.

Historically the deployable service directory used a hyphenated name. The
current repository uses the Python-safe underscored directory, so keep imports
stable while preserving compatibility with older checkouts.
"""

from __future__ import annotations

from pathlib import Path

_current_package = Path(__file__).resolve().parent
_legacy_package = Path(__file__).resolve().parents[1] / "agent-orchestration-service"

__path__ = [str(_current_package)]
if _legacy_package.exists():
    __path__.append(str(_legacy_package))
