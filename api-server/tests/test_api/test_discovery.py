"""Test discovery API endpoints"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = AsyncMock()
    return session


@pytest.fixture
def app_with_mock_db(mock_db_session):
    """App with mocked database"""
    from app.main import app
    from app.core.database import get_db

    async def mock_get_db():
        yield mock_db_session

    app.dependency_overrides[get_db] = mock_get_db
    yield app
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_discovery_requires_auth(app_with_mock_db):
    transport = ASGITransport(app=app_with_mock_db)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/discovery")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_discovery_config_requires_auth(app_with_mock_db):
    transport = ASGITransport(app=app_with_mock_db)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/discovery/config")
    assert response.status_code == 401