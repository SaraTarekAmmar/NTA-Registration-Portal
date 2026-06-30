from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.portal_test_utils import load_backend, silence_backend_logging


PORTAL_SPECS = [
    {
        "service": "admin",
        "status_path": "/api/health",
        "entry_path": "/admin-login.html",
        "expected_status": {"status": "ok", "service": "admin"},
        "expect_csrf": False,
    },
    {
        "service": "editor",
        "status_path": "/api/health",
        "entry_path": "/editor-login.html",
        "expected_status": {"status": "ok", "service": "editor"},
        "expect_csrf": False,
    },
    {
        "service": "superadmin",
        "status_path": "/api/status",
        "entry_path": "/index.html",
        "expected_status": {"status": "online", "service": "Super Admin AI Proxy"},
        "expect_csrf": False,
    },
    {
        "service": "user",
        "status_path": "/api/health",
        "entry_path": "/index.html",
        "expected_status": {"status": "ok", "service": "user"},
        "expect_csrf": True,
    },
    {
        "service": "trainer",
        "status_path": "/api/health",
        "entry_path": "/index.html",
        "expected_status": {"status": "ok", "service": "trainer"},
        "expect_csrf": False,
    },
    {
        "service": "coordinator",
        "status_path": "/api/health",
        "entry_path": "/coordinator-login.html",
        "expected_status": {"status": "ok", "service": "coordinator"},
        "expect_csrf": False,
    },
    {
        "service": "admission",
        "status_path": "/api/health",
        "entry_path": "/index.html",
        "expected_status": {"status": "ok", "service": "admission"},
        "expect_csrf": False,
    },
    {
        "service": "registration",
        "status_path": "/api/health",
        "entry_path": "/index.html",
        "expected_status": {"status": "ok", "service": "registration"},
        "expect_csrf": True,
    },
]


@pytest.mark.smoke
@pytest.mark.parametrize("spec", PORTAL_SPECS, ids=[spec["service"] for spec in PORTAL_SPECS])
def test_portal_status_entrypoint_and_source_blocking(spec, monkeypatch):
    backend = load_backend(spec["service"])
    silence_backend_logging(monkeypatch, backend)

    with TestClient(backend.app) as client:
        status_response = client.get(spec["status_path"])
        assert status_response.status_code == 200
        for key, expected_value in spec["expected_status"].items():
            assert status_response.json()[key] == expected_value

        if spec["expect_csrf"]:
            assert status_response.cookies.get("csrf_token")

        entry_response = client.get(spec["entry_path"])
        assert entry_response.status_code == 200
        assert "text/html" in entry_response.headers.get("content-type", "")

        blocked_response = client.get("/backend/main.py")
        assert blocked_response.status_code == 404
