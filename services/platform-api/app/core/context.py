"""
Request context objects for multi-tenancy, authorization, and governance.

Every request carries a TenantContext and UserContext.
These are the foundation of ABAC + minimum necessary enforcement.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from fastapi import Request

# Role hierarchy (higher can do more)
ROLE_HIERARCHY: Dict[str, int] = {
    "patient": 10,
    "billing_specialist": 20,
    "pharmacist": 25,
    "nurse": 30,
    "care_coordinator": 35,
    "clinician": 50,
    "compliance_officer": 60,
    "admin": 70,
    "super_admin": 100,
}


@dataclass(frozen=True)
class TenantContext:
    """Represents the tenant/facility scope of the current request."""
    tenant_id: str
    hospital_id: Optional[str] = None
    facility_id: Optional[str] = None
    department_id: Optional[str] = None


@dataclass(frozen=True)
class UserContext:
    """
    Authenticated user + ABAC attributes.
    This is the single source of truth for all authorization decisions.
    """
    user_id: str
    role: str
    tenant_id: str
    email: str
    full_name: str
    # ABAC attributes
    assigned_patient_ids: Set[str] = field(default_factory=set)
    assigned_departments: Set[str] = field(default_factory=set)
    assigned_facilities: Set[str] = field(default_factory=set)
    can_access_all_patients_in_tenant: bool = False
    consent_scopes: List[str] = field(default_factory=lambda: ["treatment"])
    is_break_glass: bool = False
    break_glass_reason: Optional[str] = None

    @property
    def is_clinical_role(self) -> bool:
        return self.role in {"clinician", "nurse", "care_coordinator", "pharmacist"}

    @property
    def is_admin_role(self) -> bool:
        return self.role in {"admin", "super_admin", "compliance_officer"}

    def can_access_patient(self, patient_id: str) -> bool:
        """Core ABAC check used everywhere."""
        if self.can_access_all_patients_in_tenant:
            return True
        if patient_id in self.assigned_patient_ids:
            return True
        # Patients can only access themselves
        if self.role == "patient" and self.user_id == patient_id:
            return True
        return False

    def has_minimum_role(self, required_role: str) -> bool:
        return ROLE_HIERARCHY.get(self.role, 0) >= ROLE_HIERARCHY.get(required_role, 0)


# Thread-local / contextvar storage for current request
_current_tenant: Optional[TenantContext] = None
_current_user: Optional[UserContext] = None


def set_request_context(tenant: TenantContext, user: UserContext) -> None:
    global _current_tenant, _current_user
    _current_tenant = tenant
    _current_user = user


def get_current_tenant() -> TenantContext:
    if _current_tenant is None:
        raise RuntimeError("No tenant context available. Middleware not installed?")
    return _current_tenant


def get_current_user() -> UserContext:
    if _current_user is None:
        raise RuntimeError("No user context available. Auth middleware required.")
    return _current_user


def get_current_context() -> tuple[TenantContext, UserContext]:
    return get_current_tenant(), get_current_user()


def clear_request_context() -> None:
    global _current_tenant, _current_user
    _current_tenant = None
    _current_user = None
