# ================================
# SensorPulse API - Pytest Configuration
# ================================
#
# Supports two modes:
#   1. Local (default): SQLite via aiosqlite — no Postgres needed
#   2. Container:       Real PostgreSQL — set TEST_DATABASE_URL env var
#
# When TEST_DATABASE_URL is set, tables are created via Alembic migrations
# (run before pytest in the compose command) so the latest_readings view exists.

import os
import uuid
import asyncio
from datetime import datetime, time, timezone, timedelta
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# ---------------------------------------------------------------------------
# Determine test database: Postgres (container) or SQLite (local)
# ---------------------------------------------------------------------------

_USE_POSTGRES = bool(os.environ.get("TEST_DATABASE_URL"))

if _USE_POSTGRES:
    # Container mode — use the real Postgres provided by podman-compose
    _ASYNC_DB_URL = os.environ["TEST_DATABASE_URL"]
    # Tell the app to use the same Postgres
    os.environ["DATABASE_URL"] = _ASYNC_DB_URL.replace("+asyncpg", "")
else:
    # Local mode — lightweight SQLite, no external deps
    _ASYNC_DB_URL = "sqlite+aiosqlite:///./test.db"
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"

# Shared env overrides (safe defaults)
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-jwt-signing")
os.environ.setdefault("GOOGLE_CLIENT_ID", "")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "")
os.environ.setdefault("RESEND_API_KEY", "")
os.environ.setdefault("API_DEBUG", "true")


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# Async engine for tests
# ---------------------------------------------------------------------------

test_engine = create_async_engine(_ASYNC_DB_URL, echo=False)
TestAsyncSession = sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Import models so Base.metadata knows about tables
from db.database import Base
from db.models import SensorReading, User


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """
    Create tables at session start, drop at session end.

    - SQLite mode: creates tables from ORM metadata (no views).
    - Postgres mode: tables already exist via Alembic; this is a no-op
      but we still drop+recreate to guarantee a clean slate.
    """
    if _USE_POSTGRES:
        # Alembic migrations already ran — just truncate for a clean slate
        async with test_engine.begin() as conn:
            for table in reversed(Base.metadata.sorted_tables):
                await conn.execute(table.delete())
    else:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    if _USE_POSTGRES:
        async with test_engine.begin() as conn:
            for table in reversed(Base.metadata.sorted_tables):
                await conn.execute(table.delete())
    else:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        import pathlib
        pathlib.Path("./test.db").unlink(missing_ok=True)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional DB session that rolls back after each test."""
    async with TestAsyncSession() as session:
        yield session
        await session.rollback()


# ---------------------------------------------------------------------------
# FastAPI test client
# ---------------------------------------------------------------------------

from main import app
from db.database import get_db


async def _override_get_db():
    async with TestAsyncSession() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Authenticated HTTP test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

from auth import create_access_token


@pytest.fixture
def test_user_data():
    """Standard test user data."""
    return {
        "id": str(uuid.uuid4()),
        "email": "test@example.com",
        "name": "Test User",
        "picture": None,
        "is_allowed": True,
    }


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession, test_user_data):
    """Create a test user in the database and return it."""
    user = User(
        id=uuid.UUID(test_user_data["id"]),
        email=test_user_data["email"],
        name=test_user_data["name"],
        picture=test_user_data["picture"],
        is_allowed=test_user_data["is_allowed"],
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user_data):
    """JWT Authorization header for test user."""
    token, _ = create_access_token(
        user_id=test_user_data["id"],
        email=test_user_data["email"],
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def auth_client(client: AsyncClient, test_user, auth_headers) -> AsyncClient:
    """HTTP client with auth headers pre-set (user exists in DB)."""
    client.headers.update(auth_headers)
    return client


# ---------------------------------------------------------------------------
# Sensor data helpers
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def seed_readings(db_session: AsyncSession):
    """Seed 3 devices with a few readings each."""
    now = datetime.now(timezone.utc)
    devices = [
        ("zigbee2mqtt/office", "office"),
        ("zigbee2mqtt/bedroom", "bedroom"),
        ("zigbee2mqtt/fridge", "fridge"),
    ]
    readings = []
    for topic, name in devices:
        for i in range(5):
            r = SensorReading(
                time=now - timedelta(hours=i),
                topic=topic,
                device_name=name,
                temperature=20.0 + i * 0.5 if name != "fridge" else 4.0 + i * 0.2,
                humidity=50.0 + i if name != "fridge" else None,
                battery=100 - i * 5,
                linkquality=150 - i * 10,
                raw_data={"temperature": 20.0 + i * 0.5},
            )
            readings.append(r)
            db_session.add(r)
    await db_session.commit()
    return readings
