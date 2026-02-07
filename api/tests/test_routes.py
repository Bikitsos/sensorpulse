# ================================
# SensorPulse API - Route Integration Tests
# ================================

import os

import pytest
import pytest_asyncio
from httpx import AsyncClient

_USE_POSTGRES = bool(os.environ.get("TEST_DATABASE_URL"))


# ========== Health ==========

@pytest.mark.asyncio
class TestHealthEndpoint:

    async def test_health_returns_200(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] in ("healthy", "degraded")
        assert "version" in body

    async def test_root_returns_api_info(self, client: AsyncClient):
        resp = await client.get("/")
        assert resp.status_code == 200
        assert resp.json()["name"] == "SensorPulse API"


# ========== Sensor Routes (require auth) ==========

@pytest.mark.asyncio
class TestSensorRoutes:

    async def test_devices_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/devices")
        assert resp.status_code == 401

    async def test_latest_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/latest")
        assert resp.status_code == 401

    async def test_history_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/history/office")
        assert resp.status_code == 401

    async def test_devices_returns_list(self, auth_client: AsyncClient, seed_readings):
        resp = await auth_client.get("/api/devices")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 3
        names = {d["device_name"] for d in data}
        assert names == {"office", "bedroom", "fridge"}

    async def test_latest_returns_list(self, auth_client: AsyncClient, seed_readings):
        resp = await auth_client.get("/api/latest")
        if _USE_POSTGRES:
            # Postgres has the latest_readings view from Alembic
            assert resp.status_code == 200
        else:
            # SQLite has no view — 500 is expected, but route + auth work
            assert resp.status_code in (200, 500)

    async def test_history_returns_readings(self, auth_client: AsyncClient, seed_readings):
        resp = await auth_client.get("/api/history/office", params={"hours": 48})
        assert resp.status_code == 200
        data = resp.json()
        assert data["device_name"] == "office"
        assert len(data["readings"]) == 5
        assert data["summary"]["reading_count"] == 5

    async def test_history_returns_404_for_unknown_device(self, auth_client: AsyncClient):
        resp = await auth_client.get("/api/history/nonexistent")
        assert resp.status_code == 404

    async def test_device_latest_returns_reading(self, auth_client: AsyncClient, seed_readings):
        resp = await auth_client.get("/api/devices/office/latest")
        if _USE_POSTGRES:
            assert resp.status_code == 200
        else:
            assert resp.status_code in (200, 500)


# ========== Auth Routes ==========

@pytest.mark.asyncio
class TestAuthRoutes:

    async def test_login_redirects_when_configured(self, client: AsyncClient):
        # Google OAuth not configured → should 503
        resp = await client.get("/auth/login", follow_redirects=False)
        assert resp.status_code == 503

    async def test_callback_rejects_missing_code(self, client: AsyncClient):
        resp = await client.get("/auth/callback")
        assert resp.status_code == 400

    async def test_callback_rejects_error(self, client: AsyncClient):
        resp = await client.get("/auth/callback", params={"error": "access_denied"})
        assert resp.status_code == 400

    async def test_me_requires_auth(self, client: AsyncClient):
        resp = await client.get("/auth/me")
        assert resp.status_code == 401

    async def test_me_returns_user(self, auth_client: AsyncClient):
        resp = await auth_client.get("/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "test@example.com"
        assert data["is_allowed"] is True

    async def test_logout_works(self, auth_client: AsyncClient):
        resp = await auth_client.post("/auth/logout")
        assert resp.status_code == 200

    async def test_preferences_update(self, auth_client: AsyncClient):
        resp = await auth_client.put(
            "/auth/preferences",
            json={"daily_report": True, "report_time": "09:30:00"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["daily_report"] is True


# ========== Report Routes ==========

@pytest.mark.asyncio
class TestReportRoutes:

    async def test_preview_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/report/preview")
        assert resp.status_code == 401

    async def test_preview_returns_report(self, auth_client: AsyncClient, seed_readings):
        resp = await auth_client.get("/api/report/preview")
        assert resp.status_code == 200
        data = resp.json()
        assert "sensors" in data
        assert "alerts" in data

    async def test_preview_html(self, auth_client: AsyncClient, seed_readings):
        resp = await auth_client.get("/api/report/preview/html")
        assert resp.status_code == 200
        assert "SensorPulse" in resp.text

    async def test_send_now_fails_without_resend(self, auth_client: AsyncClient, seed_readings):
        # RESEND_API_KEY is empty in test env
        resp = await auth_client.post("/api/report/send-now")
        assert resp.status_code == 503
