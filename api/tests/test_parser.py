# ================================
# SensorPulse Ingester - Payload Parser Tests
# ================================

import sys
import os
from datetime import datetime, timezone

import pytest

# Add ingester directory to path so we can import parser
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ingester"))

# Stub the logger module that parser imports (it depends on structlog config)
import types
_stub = types.ModuleType("logger")
_stub.logger = types.SimpleNamespace(
    debug=lambda *a, **kw: None,
    info=lambda *a, **kw: None,
    error=lambda *a, **kw: None,
)
sys.modules["logger"] = _stub

from parser import PayloadParser, ParsedReading


@pytest.fixture
def parser():
    return PayloadParser()


# ========== ParsedReading ==========

class TestParsedReading:

    def test_is_valid_with_temperature(self):
        r = ParsedReading(topic="t", time=datetime.now(timezone.utc), temperature=22.0)
        assert r.is_valid() is True

    def test_is_valid_with_humidity(self):
        r = ParsedReading(topic="t", time=datetime.now(timezone.utc), humidity=55.0)
        assert r.is_valid() is True

    def test_is_valid_with_battery_only(self):
        r = ParsedReading(topic="t", time=datetime.now(timezone.utc), battery=80)
        assert r.is_valid() is True

    def test_is_not_valid_when_empty(self):
        r = ParsedReading(topic="t", time=datetime.now(timezone.utc))
        assert r.is_valid() is False


# ========== Topic Filtering ==========

class TestTopicFiltering:

    def test_ignore_availability(self, parser):
        assert parser.should_ignore_topic("zigbee2mqtt/sensor/availability") is True

    def test_ignore_bridge_state(self, parser):
        assert parser.should_ignore_topic("zigbee2mqtt/bridge/state") is True

    def test_ignore_bridge_logging(self, parser):
        assert parser.should_ignore_topic("zigbee2mqtt/bridge/logging") is True

    def test_allow_sensor_topic(self, parser):
        assert parser.should_ignore_topic("zigbee2mqtt/office_sensor") is False


# ========== Device Name Extraction ==========

class TestDeviceNameExtraction:

    def test_standard_topic(self, parser):
        assert parser.extract_device_name("zigbee2mqtt/office") == "office"

    def test_nested_topic(self, parser):
        assert parser.extract_device_name("zigbee2mqtt/floor1/bedroom") == "bedroom"

    def test_single_segment(self, parser):
        assert parser.extract_device_name("sensor1") == "sensor1"


# ========== Payload Parsing ==========

class TestPayloadParsing:

    def test_type_a_full_payload(self, parser):
        payload = {
            "battery": 100,
            "humidity": 61,
            "linkquality": 104,
            "temperature": 17,
            "temperature_calibration": 0,
            "temperature_units": "celsius",
            "voltage": 2900,
        }
        reading = parser.parse("zigbee2mqtt/office", payload)
        assert reading is not None
        assert reading.temperature == 17.0
        assert reading.humidity == 61.0
        assert reading.battery == 100
        assert reading.linkquality == 104
        assert reading.device_name == "office"

    def test_type_b_minimal_payload(self, parser):
        payload = {
            "battery": 100,
            "linkquality": 156,
            "temperature": 6.2,
            "temperature_calibration": 0,
            "temperature_units": "celsius",
        }
        reading = parser.parse("zigbee2mqtt/fridge", payload)
        assert reading is not None
        assert reading.temperature == 6.2
        assert reading.humidity is None
        assert reading.battery == 100
        assert reading.device_name == "fridge"

    def test_empty_payload_returns_none(self, parser):
        assert parser.parse("zigbee2mqtt/sensor", {}) is None

    def test_none_payload_returns_none(self, parser):
        assert parser.parse("zigbee2mqtt/sensor", None) is None

    def test_ignored_topic_returns_none(self, parser):
        payload = {"temperature": 22}
        assert parser.parse("zigbee2mqtt/bridge/state", payload) is None

    def test_no_useful_data_returns_none(self, parser):
        payload = {"action": "toggle", "click": "single"}
        assert parser.parse("zigbee2mqtt/button", payload) is None

    def test_battery_low_boolean_true(self, parser):
        payload = {"battery_low": True, "temperature": 20}
        reading = parser.parse("zigbee2mqtt/sensor", payload)
        assert reading.battery == 10

    def test_battery_low_boolean_false(self, parser):
        payload = {"battery_low": False, "temperature": 20}
        reading = parser.parse("zigbee2mqtt/sensor", payload)
        assert reading.battery == 100

    def test_raw_data_preserved(self, parser):
        payload = {"temperature": 22, "custom_field": "value"}
        reading = parser.parse("zigbee2mqtt/sensor", payload)
        assert reading.raw_data == payload

    def test_alternative_temperature_field(self, parser):
        payload = {"device_temperature": 35}
        reading = parser.parse("zigbee2mqtt/router", payload)
        assert reading is not None
        assert reading.temperature == 35.0

    def test_soil_moisture_as_humidity(self, parser):
        payload = {"soil_moisture": 42}
        reading = parser.parse("zigbee2mqtt/plant", payload)
        assert reading is not None
        assert reading.humidity == 42.0

    def test_stats_increment(self, parser):
        parser.parse("zigbee2mqtt/s", {"temperature": 20})
        parser.parse("zigbee2mqtt/s", {"temperature": 21})
        stats = parser.get_stats()
        assert stats["parsed"] == 2
        assert stats["errors"] == 0
