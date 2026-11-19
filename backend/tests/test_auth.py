"""Unit tests for authentication, JWT issuance, and RBAC."""
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_admin_login_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/auth/login",
            json={"email": "admin@infrasphere.bd", "password": "Demo1234!"},
        )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["role"] == "admin"


@pytest.mark.asyncio
async def test_invalid_login_fails():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/auth/login",
            json={"email": "admin@infrasphere.bd", "password": "WrongPassword!"},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_register_user_success_and_duplicate_conflict():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Register new operator
        response = await ac.post(
            "/api/v1/auth/register",
            json={
                "email": "field_lead@infrasphere.bd",
                "password": "SecurePassword123!",
                "full_name": "Field Commander Rafiq",
                "role": "field_coordinator",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "field_lead@infrasphere.bd"
        assert data["user"]["role"] == "field_coordinator"

        # Try registering same email again -> Conflict 409
        dup_resp = await ac.post(
            "/api/v1/auth/register",
            json={
                "email": "field_lead@infrasphere.bd",
                "password": "AnotherPassword!",
                "full_name": "Duplicate Rafiq",
                "role": "field_coordinator",
            },
        )
        assert dup_resp.status_code == 409
