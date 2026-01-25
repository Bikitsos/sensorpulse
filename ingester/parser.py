# ================================
# SensorPulse Ingester - Payload Parser
# ================================

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from dataclasses import dataclass

from logger import logger


@dataclass
class ParsedReading:
    """
    Structured sensor reading extracted from MQTT payload.
    """
    topic: str
    time: datetime
    device_name: str = ""
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    battery: Optional[int] = None
    linkquality: Optional[int] = None
    raw_data: Optional[Dict[str, Any]] = None
    
    def is_valid(self) -> bool:
        """Check if reading has at least some useful data."""
        return any([
            self.temperature is not None,
            self.humidity is not None,
            self.battery is not None,
        ])


class PayloadParser:
    """
    Parser for Zigbee2MQTT sensor payloads.
    
    Handles two main payload types:
    - Type A (Full): Contains comfort metrics, update status, etc.
    - Type B (Minimal): Contains only temp/battery basics.
    """
    
    # Topics to ignore (bridge status, availability, etc.)
    IGNORED_TOPIC_SUFFIXES = [
        "/availability",
        "/bridge/state",
        "/bridge/info",
        "/bridge/logging",
        "/bridge/devices",
        "/bridge/groups",
        "/bridge/extensions",
        "/bridge/config",
    ]
    
    def __init__(self):
        self.parse_count = 0
        self.error_count = 0
    
    def should_ignore_topic(self, topic: str) -> bool:
        """Check if topic should be ignored (non-sensor data)."""
        for suffix in self.IGNORED_TOPIC_SUFFIXES:
            if topic.endswith(suffix):
                return True
        return False
    
    def extract_device_name(self, topic: str) -> str:
        """Extract device name from topic (e.g., 'zigbee2mqtt/sensor1' -> 'sensor1')."""
        parts = topic.split("/")
        if len(parts) >= 2:
            return parts[-1]
        return topic
    
    def parse(self, topic: str, payload: Dict[str, Any]) -> Optional[ParsedReading]:
        """
        Parse MQTT payload into structured reading.
        
        Args:
            topic: MQTT topic string
            payload: Decoded JSON payload
            
        Returns:
            ParsedReading if valid sensor data, None otherwise
        """
        try:
            # Skip non-sensor topics
            if self.should_ignore_topic(topic):
                logger.debug("Ignoring topic", topic=topic)
                return None
            
            # Skip empty payloads
            if not payload:
                logger.debug("Empty payload", topic=topic)
                return None
            
            # Create reading with timestamp and device name
            reading = ParsedReading(
                topic=topic,
                time=datetime.now(timezone.utc),
                device_name=self.extract_device_name(topic),
                raw_data=payload,
            )
            
            # Extract temperature (multiple possible field names)
            reading.temperature = self._extract_float(payload, [
                "temperature",
                "device_temperature",
                "local_temperature",
                "current_heating_setpoint",
            ])
            
            # Extract humidity
            reading.humidity = self._extract_float(payload, [
                "humidity",
                "soil_moisture",
            ])
            
            # Extract battery
            reading.battery = self._extract_int(payload, [
                "battery",
                "battery_low",  # Some devices use boolean
            ])
            
            # Handle battery_low boolean
            if reading.battery is None and "battery_low" in payload:
                reading.battery = 10 if payload["battery_low"] else 100
            
            # Extract link quality
            reading.linkquality = self._extract_int(payload, [
                "linkquality",
                "link_quality",
            ])
            
            # Validate reading has useful data
            if not reading.is_valid():
                logger.debug(
                    "Payload has no extractable sensor data",
                    topic=topic,
                    payload_keys=list(payload.keys()),
                )
                return None
            
            self.parse_count += 1
            logger.debug(
                "Parsed reading",
                topic=topic,
                temp=reading.temperature,
                humidity=reading.humidity,
                battery=reading.battery,
            )
            
            return reading
            
        except Exception as e:
            self.error_count += 1
            logger.error(
                "Failed to parse payload",
                topic=topic,
                error=str(e),
                payload_preview=str(payload)[:200],
            )
            return None
    
    def _extract_float(
        self,
        payload: Dict[str, Any],
        field_names: list,
    ) -> Optional[float]:
        """Extract float value from payload, trying multiple field names."""
        for name in field_names:
            if name in payload:
                try:
                    value = payload[name]
                    if value is not None:
                        return float(value)
                except (ValueError, TypeError):
                    continue
        return None
    
    def _extract_int(
        self,
        payload: Dict[str, Any],
        field_names: list,
    ) -> Optional[int]:
        """Extract integer value from payload, trying multiple field names."""
        for name in field_names:
            if name in payload:
                try:
                    value = payload[name]
                    if value is not None:
                        return int(value)
                except (ValueError, TypeError):
                    continue
        return None
    
    def get_stats(self) -> Dict[str, int]:
        """Return parser statistics."""
        return {
            "parsed": self.parse_count,
            "errors": self.error_count,
        }
