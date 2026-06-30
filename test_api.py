import pytest
from httpx import AsyncClient
import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'admin', 'backend'))

try:
    from main import app as admin_app
except ImportError:
    admin_app = None

@pytest.mark.asyncio
async def test_admin_api_requires_auth():
    if not admin_app:
        pytest.skip("Admin app not found in path")
    async with AsyncClient(app=admin_app, base_url="http://test") as ac:
        response = await ac.get("/api/admin/registration-stats")
    # Should be 401 Unauthorized because no token is provided
    assert response.status_code == 401
    assert "Not authenticated" in response.text or "Could not validate credentials" in response.text

@pytest.mark.asyncio
async def test_login_validation_failure():
    if not admin_app:
        pytest.skip("Admin app not found in path")
    async with AsyncClient(app=admin_app, base_url="http://test") as ac:
        response = await ac.post("/api/admin/auth/login", json={"email": "bad@email.com", "nationalId": "123", "password": "wrong"})
    # Should fail validation or return 401
    assert response.status_code in [401, 404, 422]
