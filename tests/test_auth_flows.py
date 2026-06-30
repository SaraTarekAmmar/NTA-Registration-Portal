from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.portal_test_utils import (
    FakeDB,
    build_user_row,
    load_backend,
    loaded_module,
    silence_backend_logging,
)


AUTH_CASES = [
    {
        "name": "admin",
        "service": "admin",
        "route_module": "core.auth",
        "path": "/api/admin/auth/login",
        "payload": {
            "email": "admin@nta.edu.eg",
            "nationalId": "29001011234567",
            "password": "NTA@Admin2026",
        },
        "user_row": build_user_row(
            role="admin",
            email="admin@nta.edu.eg",
            national_id="29001011234567",
            full_name="Admin User",
            user_id=1,
        ),
        "expected": {
            "role": "admin",
            "fullName": "Admin User",
            "userId": 1,
        },
    },
    {
        "name": "editor",
        "service": "editor",
        "route_module": "routers.auth",
        "path": "/api/editor/auth/login",
        "payload": {
            "email": "editor@nta.edu.eg",
            "nationalId": "29505051234567",
            "password": "NTA@Editor2026",
        },
        "user_row": build_user_row(
            role="editor",
            email="editor@nta.edu.eg",
            national_id="29505051234567",
            full_name="Editor User",
            user_id=2,
        ),
        "expected": {
            "role": "editor",
            "fullName": "Editor User",
            "userId": 2,
        },
    },
    {
        "name": "superadmin",
        "service": "superadmin",
        "route_module": "routers.auth",
        "path": "/api/auth/login",
        "payload": {
            "email": "superadmin@nta.edu.eg",
            "password": "NTA@Super2026",
        },
        "user_row": build_user_row(
            role="superadmin",
            email="superadmin@nta.edu.eg",
            full_name="Super Admin",
            user_id=3,
        ),
        "expected": {
            "role": "superadmin",
            "fullName": "Super Admin",
        },
    },
    {
        "name": "trainee",
        "service": "user",
        "route_module": "core.auth",
        "path": "/api/auth/login",
        "payload": {
            "email": "trainee@nta.edu.eg",
            "nationalId": "30101011234567",
            "password": "NTA@Trainee2026",
            "role": "trainee",
        },
        "user_row": build_user_row(
            role="trainee",
            email="trainee@nta.edu.eg",
            national_id="30101011234567",
            full_name="Trainee User",
            user_id=4,
        ),
        "expected": {
            "role": "trainee",
            "fullName": "Trainee User",
            "userId": 4,
        },
    },
    {
        "name": "trainer",
        "service": "trainer",
        "route_module": "core.auth",
        "path": "/api/auth/login",
        "payload": {
            "email": "trainer@nta.edu.eg",
            "nationalId": "30201011234567",
            "password": "NTA@Trainer2026",
            "role": "trainer",
        },
        "user_row": build_user_row(
            role="trainer",
            email="trainer@nta.edu.eg",
            national_id="30201011234567",
            full_name="Trainer User",
            user_id=5,
        ),
        "expected": {
            "role": "trainer",
            "fullName": "Trainer User",
            "userId": 5,
        },
    },
    {
        "name": "coordinator",
        "service": "coordinator",
        "route_module": "routers.auth",
        "path": "/api/coordinator/auth/login",
        "payload": {
            "email": "coordinator@nta.edu.eg",
            "nationalId": "29304041234567",
            "password": "NTA@Coord2026",
        },
        "user_row": build_user_row(
            role="coordinator",
            email="coordinator@nta.edu.eg",
            national_id="29304041234567",
            full_name="Coordinator User",
            user_id=6,
        ),
        "expected": {
            "role": "coordinator",
            "fullName": "Coordinator User",
            "userId": 6,
        },
    },
    {
        "name": "admission_manager",
        "service": "admission",
        "route_module": "core.auth",
        "path": "/api/auth/login",
        "payload": {
            "email": "admission@nta.edu.eg",
            "nationalId": "29402021234567",
            "password": "NTA@Admission2026",
            "role": "admission_manager",
        },
        "user_row": build_user_row(
            role="admission_manager",
            email="admission@nta.edu.eg",
            national_id="29402021234567",
            full_name="Admission Manager",
            user_id=7,
        ),
        "expected": {
            "role": "admission_manager",
            "fullName": "Admission Manager",
            "userId": 7,
        },
    },
]


def patch_auth_dependencies(monkeypatch, module_name: str, user_row: dict, token_label: str):
    route_module = loaded_module(module_name)
    fake_db = FakeDB(user_row)

    monkeypatch.setattr(route_module, "get_db_connection", lambda: fake_db)

    if hasattr(route_module, "check_rate_limit"):
        monkeypatch.setattr(route_module, "check_rate_limit", lambda *args, **kwargs: True)
    if hasattr(route_module, "record_login_attempt"):
        monkeypatch.setattr(route_module, "record_login_attempt", lambda *args, **kwargs: None)
    if hasattr(route_module, "verify_password"):
        monkeypatch.setattr(route_module, "verify_password", lambda *args, **kwargs: True)
    if hasattr(route_module, "create_access_token"):
        monkeypatch.setattr(route_module, "create_access_token", lambda data: f"token-{token_label}")
    if hasattr(route_module, "log_activity"):
        monkeypatch.setattr(route_module, "log_activity", lambda *args, **kwargs: None)

    return fake_db


@pytest.mark.unit
@pytest.mark.parametrize("case", AUTH_CASES, ids=[case["name"] for case in AUTH_CASES])
def test_login_flows_return_expected_payload(case, monkeypatch):
    backend = load_backend(case["service"])
    silence_backend_logging(monkeypatch, backend)
    patch_auth_dependencies(monkeypatch, case["route_module"], case["user_row"], case["name"])

    with TestClient(backend.app) as client:
        response = client.post(case["path"], json=case["payload"])

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["access_token"] == f"token-{case['name']}"
    assert body["token_type"] == "bearer"
    for key, expected_value in case["expected"].items():
        assert body[key] == expected_value


@pytest.mark.unit
def test_trainee_portal_rejects_non_trainee_role(monkeypatch):
    backend = load_backend("user")
    silence_backend_logging(monkeypatch, backend)
    patch_auth_dependencies(
        monkeypatch,
        "core.auth",
        build_user_row(
            role="trainer",
            email="trainer@nta.edu.eg",
            national_id="30201011234567",
            full_name="Trainer User",
            user_id=8,
        ),
        "role-mismatch-user",
    )

    with TestClient(backend.app) as client:
        response = client.post(
            "/api/auth/login",
            json={
                "email": "trainer@nta.edu.eg",
                "nationalId": "30201011234567",
                "password": "NTA@Trainer2026",
                "role": "trainer",
            },
        )

    assert response.status_code == 403
    assert "هذه البوابة" in response.json()["detail"]


@pytest.mark.unit
def test_trainer_portal_rejects_non_trainer_role(monkeypatch):
    backend = load_backend("trainer")
    silence_backend_logging(monkeypatch, backend)
    patch_auth_dependencies(
        monkeypatch,
        "core.auth",
        build_user_row(
            role="trainee",
            email="trainee@nta.edu.eg",
            national_id="30101011234567",
            full_name="Trainee User",
            user_id=9,
        ),
        "role-mismatch-trainer",
    )

    with TestClient(backend.app) as client:
        response = client.post(
            "/api/auth/login",
            json={
                "email": "trainee@nta.edu.eg",
                "nationalId": "30101011234567",
                "password": "NTA@Trainee2026",
                "role": "trainee",
            },
        )

    assert response.status_code == 403
    assert "هذه البوابة" in response.json()["detail"]
