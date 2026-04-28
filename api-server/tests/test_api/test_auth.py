"""Test auth API endpoints"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch
from app.models.user import User, UserRole


@pytest.fixture
def mock_user_repo():
    """Mock user repository"""
    repo = MagicMock()
    repo.get_by_username = AsyncMock(return_value=None)
    repo.create = AsyncMock()
    return repo


@pytest.fixture
def app_with_mock_repo(mock_user_repo):
    """App with mocked database and repository"""
    from app.main import app
    from app.core.database import get_db

    async def mock_get_db():
        yield AsyncMock()

    app.dependency_overrides[get_db] = mock_get_db
    yield app
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_login_invalid_credentials(app_with_mock_repo, mock_user_repo):
    """Test login with invalid credentials returns 401"""
    with patch("app.api.auth.UserRepository", return_value=mock_user_repo):
        transport = ASGITransport(app=app_with_mock_repo)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/auth/login",
                json={"username": "nonexistent", "password": "wrong"},
            )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_without_token(app_with_mock_repo):
    """Test /me endpoint without token returns 401"""
    transport = ASGITransport(app=app_with_mock_repo)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/auth/me")
    # FastAPI returns 401 for missing credentials
    assert response.status_code == 401