"""Security helpers for the memory service."""

from __future__ import annotations


def assert_same_tenant(request_tenant_id: str, record_tenant_id: str) -> None:
    if request_tenant_id != record_tenant_id:
        raise PermissionError("Cross-tenant memory access denied")

