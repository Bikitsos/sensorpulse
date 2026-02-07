# ================================
# SensorPulse API - Schema Unit Tests
# ================================

from datetime import datetime, timezone, time
from uuid import uuid4

import pytest
from pydantic import ValidationError
from schemas import (
    SensorReadingBase,
    SensorReading,
    SensorLatest,
    DeviceInfo,
    HistoryQuery,
    HistorySummary,
    UserBase,
    User,
    UserPreferences,
    Token,
    TokenData,
    GoogleUser,
    ReportSummary,
    DailyReport,
)


class TestSensorSchemas:

    def test_sensor_reading_base_minimal(self):
        r = SensorReadingBase(topic="zigbee2mqtt/office", device_name="office")
        assert r.temperature is None
        assert r.humidity is None

    def test_sensor_reading_full(self):
        now = datetime.now(timezone.utc)
        r = SensorReading(
            topic="zigbee2mqtt/office",
            device_name="office",
            time=now,
            temperature=22.5,
            humidity=55.0,
            battery=90,
            linkquality=120,
            raw_data={"temperature": 22.5},
        )
        assert r.temperature == 22.5
        assert r.raw_data["temperature"] == 22.5

    def test_sensor_latest_includes_last_seen(self):
        sl = SensorLatest(
            topic="t", device_name="d", time=datetime.now(timezone.utc),
            last_seen_minutes=5,
        )
        assert sl.last_seen_minutes == 5

    def test_history_query_defaults(self):
        q = HistoryQuery()
        assert q.hours == 24
        assert q.resolution is None

    def test_history_query_rejects_out_of_range(self):
        with pytest.raises(ValidationError):
            HistoryQuery(hours=0)
        with pytest.raises(ValidationError):
            HistoryQuery(hours=200)

    def test_history_query_rejects_bad_resolution(self):
        with pytest.raises(ValidationError):
            HistoryQuery(resolution="2h")


class TestUserSchemas:

    def test_user_preferences_all_optional(self):
        p = UserPreferences()
        assert p.daily_report is None
        assert p.report_time is None

    def test_user_preferences_partial(self):
        p = UserPreferences(daily_report=True)
        assert p.daily_report is True

    def test_google_user_valid(self):
        g = GoogleUser(id="123", email="user@gmail.com", name="Test")
        assert g.email == "user@gmail.com"

    def test_google_user_rejects_bad_email(self):
        with pytest.raises(ValidationError):
            GoogleUser(id="123", email="not-an-email")


class TestReportSchemas:

    def test_report_summary_defaults(self):
        rs = ReportSummary(
            device_name="office",
            last_seen=datetime.now(timezone.utc),
        )
        assert rs.is_offline is False
        assert rs.battery is None

    def test_daily_report_empty_sensors(self):
        now = datetime.now(timezone.utc)
        dr = DailyReport(
            generated_at=now,
            period_start=now,
            period_end=now,
            sensors=[],
        )
        assert len(dr.sensors) == 0
        assert dr.alerts == []


class TestTokenSchemas:

    def test_token_response(self):
        t = Token(access_token="abc", expires_in=3600)
        assert t.token_type == "bearer"

    def test_token_data(self):
        td = TokenData(
            user_id="uid",
            email="e@e.com",
            exp=datetime.now(timezone.utc),
        )
        assert td.user_id == "uid"
