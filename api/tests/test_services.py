# ================================
# SensorPulse API - Service Layer Tests
# ================================

import uuid
from datetime import datetime, timezone, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from services import SensorService, UserService
from db.models import SensorReading, User


@pytest.mark.asyncio
class TestSensorService:

    async def test_get_devices_empty(self, db_session: AsyncSession):
        svc = SensorService(db_session)
        devices = await svc.get_devices()
        assert devices == []

    async def test_get_devices_returns_all(self, db_session: AsyncSession, seed_readings):
        svc = SensorService(db_session)
        devices = await svc.get_devices()
        assert len(devices) == 3
        names = {d["device_name"] for d in devices}
        assert "office" in names

    async def test_get_device_history(self, db_session: AsyncSession, seed_readings):
        svc = SensorService(db_session)
        history = await svc.get_device_history("office", hours=48)
        assert history["device_name"] == "office"
        assert len(history["readings"]) == 5
        assert history["summary"]["reading_count"] == 5
        assert history["summary"]["min_temp"] is not None

    async def test_get_device_history_empty(self, db_session: AsyncSession):
        svc = SensorService(db_session)
        history = await svc.get_device_history("nonexistent", hours=24)
        assert len(history["readings"]) == 0
        assert history["summary"]["reading_count"] == 0

    async def test_history_summary_stats(self, db_session: AsyncSession, seed_readings):
        svc = SensorService(db_session)
        history = await svc.get_device_history("office", hours=48)
        s = history["summary"]
        assert s["min_temp"] <= s["avg_temp"] <= s["max_temp"]

    async def test_fridge_has_no_humidity(self, db_session: AsyncSession, seed_readings):
        svc = SensorService(db_session)
        history = await svc.get_device_history("fridge", hours=48)
        s = history["summary"]
        assert s["min_humidity"] is None


@pytest.mark.asyncio
class TestUserService:

    async def test_create_user(self, db_session: AsyncSession):
        svc = UserService(db_session)
        user = await svc.create_or_update("new@example.com", name="New")
        assert user.email == "new@example.com"
        assert user.is_allowed is False  # new users not auto-approved

    async def test_get_by_email(self, db_session: AsyncSession):
        svc = UserService(db_session)
        await svc.create_or_update("find@example.com", name="Find Me")
        found = await svc.get_by_email("find@example.com")
        assert found is not None
        assert found.name == "Find Me"

    async def test_get_by_email_not_found(self, db_session: AsyncSession):
        svc = UserService(db_session)
        assert await svc.get_by_email("ghost@example.com") is None

    async def test_update_existing_user(self, db_session: AsyncSession):
        svc = UserService(db_session)
        u1 = await svc.create_or_update("dup@example.com", name="V1")
        u2 = await svc.create_or_update("dup@example.com", name="V2")
        assert u1.id == u2.id
        assert u2.name == "V2"

    async def test_get_by_id(self, db_session: AsyncSession):
        svc = UserService(db_session)
        user = await svc.create_or_update("id@example.com")
        found = await svc.get_by_id(str(user.id))
        assert found is not None
        assert found.email == "id@example.com"

    async def test_update_preferences(self, db_session: AsyncSession):
        svc = UserService(db_session)
        user = await svc.create_or_update("prefs@example.com")
        updated = await svc.update_preferences(
            str(user.id), daily_report=True,
        )
        assert updated.daily_report is True

    async def test_update_preferences_nonexistent(self, db_session: AsyncSession):
        svc = UserService(db_session)
        result = await svc.update_preferences(str(uuid.uuid4()), daily_report=True)
        assert result is None
