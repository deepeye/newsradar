"""Test configuration and fixtures"""
import pytest
from httpx import AsyncClient, ASGITransport


@pytest.fixture
async def client():
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def auth_token(client: AsyncClient):
    """Get auth token for protected endpoints (requires running DB with init_db)"""
    # This will only work with a running database
    # In CI, use test database with seed data
    response = await client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None