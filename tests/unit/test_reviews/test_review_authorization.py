from app.api.v1.reviews import _can_resolve_review, _can_view_review


def test_admin_cannot_view_or_resolve_clinical_review_by_default():
    assert _can_view_review("admin", "clinician") is False
    assert _can_resolve_review("admin", "clinician") is False


def test_compliance_can_view_and_resolve_review_metadata():
    assert _can_view_review("compliance_officer", "clinician") is True
    assert _can_resolve_review("compliance_officer", "clinician") is True


def test_clinical_roles_can_resolve_assigned_clinical_review():
    assert _can_view_review("clinician", "clinician") is True
    assert _can_resolve_review("clinician", "clinician") is True
