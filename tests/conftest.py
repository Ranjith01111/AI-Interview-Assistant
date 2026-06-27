"""
Test Configuration & Shared Fixtures

Provides:
  • Async SQLite test database (in-memory)
  • Redis mock
  • FastAPI TestClient with dependency overrides
  • Factory fixtures for users, sessions, etc.
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.db.base import Base
from backend.core.config import settings

# Override settings for testing
settings.DEBUG = False  # Ensure debug mode is OFF during tests
settings.JWT_SECRET_KEY = "test_jwt_secret_key_for_unit_tests_only_128_chars_long_padding_here"
settings.SECRET_KEY = "test_secret_key_64_hex_chars_padding_here_for_testing"


# ── Async Event Loop ─────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── Test Database (SQLite Async In-Memory) ───────────────────────────────

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides a clean database session for each test."""
    # Import all models so tables are registered
    import backend.models  # noqa: F401

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ── Redis Mock ───────────────────────────────────────────────────────────

@pytest.fixture
def mock_redis():
    """Mock Redis operations for tests that don't need real Redis."""
    redis_store = {}

    async def mock_set_json(key, value, ttl=None):
        redis_store[key] = value

    async def mock_get_json(key):
        return redis_store.get(key)

    async def mock_delete(key):
        redis_store.pop(key, None)

    with patch("backend.services.auth_service.redis_set_json", side_effect=mock_set_json), \
         patch("backend.services.auth_service.redis_get_json", side_effect=mock_get_json), \
         patch("backend.services.auth_service.redis_delete", side_effect=mock_delete), \
         patch("backend.services.session_service.get_agent_state", return_value=None), \
         patch("backend.services.session_service.save_agent_state", new_callable=AsyncMock):
        yield redis_store


# ── FastAPI Test Client ──────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client(db_session: AsyncSession, mock_redis) -> AsyncGenerator[AsyncClient, None]:
    """
    Provides an async HTTP client wired to the test database.
    All auth routes, interview routes, etc. use the test DB.
    """
    from backend.main import app
    from backend.db.session import get_db

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()


# ── Factory Fixtures ─────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def candidate_user(db_session: AsyncSession):
    """Creates a test candidate user in the DB."""
    from backend.models.user import User, UserRole
    from backend.services.auth_service import hash_password

    user = User(
        id=uuid.uuid4(),
        name="Test Candidate",
        email="candidate@test.com",
        password_hash=hash_password("TestPass123!"),
        role=UserRole.CANDIDATE.value,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession):
    """Creates a test admin user in the DB."""
    from backend.models.user import User, UserRole
    from backend.services.auth_service import hash_password

    user = User(
        id=uuid.uuid4(),
        name="Test Admin",
        email="admin@test.com",
        password_hash=hash_password("AdminPass123!"),
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def recruiter_user(db_session: AsyncSession):
    """Creates a test recruiter user in the DB."""
    from backend.models.user import User, UserRole
    from backend.services.auth_service import hash_password

    user = User(
        id=uuid.uuid4(),
        name="Test Recruiter",
        email="recruiter@test.com",
        password_hash=hash_password("RecruiterPass123!"),
        role=UserRole.RECRUITER.value,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


def make_auth_header(user) -> dict:
    """Generate a valid JWT token for the given user and return as headers."""
    from backend.services.auth_service import create_access_token
    token = create_access_token(user.id, user.role)
    return {"Authorization": f"Bearer {token}"}
