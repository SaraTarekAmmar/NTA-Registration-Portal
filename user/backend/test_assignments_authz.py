"""RBAC regression tests for the assignments router guard.

Locks in the fix that made /api/assignments authoring endpoints require a
trainer-or-staff token. Runs without hitting the DB — it exercises the guard
function directly. Run: `python -m pytest test_assignments_authz.py` or
`python test_assignments_authz.py`.
"""
from fastapi import HTTPException
from routers.assignments import require_trainer_or_staff, _TRAINER_OR_STAFF

ALLOWED = ["trainer", "admin", "editor", "superadmin"]
DENIED = ["trainee", "applicant", "coordinator", "committee_member", ""]


def test_allowed_roles_pass():
    for role in ALLOWED:
        user = {"id": 1, "role": role}
        assert require_trainer_or_staff(user) is user, f"{role} should be allowed"


def test_denied_roles_get_403():
    for role in DENIED:
        try:
            require_trainer_or_staff({"id": 2, "role": role})
        except HTTPException as exc:
            assert exc.status_code == 403, f"{role} should be 403, got {exc.status_code}"
        else:
            raise AssertionError(f"{role} should have been rejected with 403")


def test_role_set_matches_expectation():
    assert _TRAINER_OR_STAFF == set(ALLOWED)


if __name__ == "__main__":
    test_allowed_roles_pass()
    test_denied_roles_get_403()
    test_role_set_matches_expectation()
    print("All assignments authz tests passed.")
