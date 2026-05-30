"""Shared test path bootstrap for the monorepo."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLATFORM_API = ROOT / "services" / "platform-api"

for path in (ROOT, PLATFORM_API):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

