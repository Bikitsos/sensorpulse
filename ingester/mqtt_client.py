# ================================
# SensorPulse Ingester - MQTT Client
# ================================

import json
import asyncio
from datetime import datetime
from typing import Callable, Optional, Dict, Any

import paho.mqtt.client as mqtt

from config import settings
from logger import logger


class MQTTClient:
    """
    MQTT client for connecting to Zigbee2MQTT broker.
    
    Features:
    - Automatic reconnection
    - Message callback handling
    - Connection statistics
    - Last will and testament
    """
    
    def __init__(self):
        self.client: Optional[mqtt.Client] = None
        self._connected = False
        self._message_callback: Optional[Callable] = None
        self._message_count = 0
        self._error_count = 0
        self._connect_time: Optional[datetime] = None
        self._last_message_time: Optional[datetime] = None
    
    def set_message_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """
        Set callback for incoming messages.
        
        Args:
            callback: Function(topic: str, payload: dict) called for each message
        """
        self._message_callback = callback
    
    def connect(self) -> bool:
        """
        Connect to MQTT broker.
        
        Returns:
            True if connection initiated, False on error
        """
        try:
            # Create client with callback API version
            self.client = mqtt.Client(
                client_id=settings.mqtt_client_id,
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            )
            
            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            # Set authentication if provided
            if settings.mqtt_user and settings.mqtt_pass:
                self.client.username_pw_set(
                    settings.mqtt_user,
                    settings.mqtt_pass,
                )
            
            # Set last will (indicates ingester status)
            self.client.will_set(
                topic="sensorpulse/ingester/status",
                payload=json.dumps({"status": "offline"}),
                qos=1,
                retain=True,
            )
            
            logger.info(
                "Connecting to MQTT broker",
                broker=settings.mqtt_broker_ip,
                port=settings.mqtt_port,
            )
            
            # Connect (non-blocking)
            self.client.connect_async(
                settings.mqtt_broker_ip,
                settings.mqtt_port,
                keepalive=60,
            )
            
            return True
            
        except Exception as e:
            logger.error("Failed to initialize MQTT client", error=str(e))
            return False
    
    def start(self):
        """Start the MQTT client loop (non-blocking)."""
        if self.client:
            self.client.loop_start()
            logger.info("MQTT client loop started")
    
    def stop(self):
        """Stop the MQTT client and disconnect."""
        if self.client:
            # Publish offline status
            self.client.publish(
                "sensorpulse/ingester/status",
                json.dumps({"status": "offline"}),
                qos=1,
                retain=True,
            )
            self.client.loop_stop()
            self.client.disconnect()
            self._connected = False
            logger.info("MQTT client stopped")
    
    def _on_connect(self, client, userdata, flags, reason_code, properties):
        """Callback when connected to broker."""
        if reason_code == 0:
            self._connected = True
            self._connect_time = datetime.utcnow()
            
            logger.info(
                "Connected to MQTT broker",
                broker=settings.mqtt_broker_ip,
            )
            
            # Subscribe to configured topic
            client.subscribe(settings.mqtt_topic, qos=1)
            logger.info("Subscribed to topic", topic=settings.mqtt_topic)
            
            # Publish online status
            client.publish(
                "sensorpulse/ingester/status",
                json.dumps({
                    "status": "online",
                    "connected_at": self._connect_time.isoformat(),
                }),
                qos=1,
                retain=True,
            )
        else:
            self._connected = False
            logger.error(
                "Failed to connect to MQTT broker",
                reason_code=reason_code,
            )
    
    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        """Callback when disconnected from broker."""
        self._connected = False
        logger.warning(
            "Disconnected from MQTT broker",
            reason_code=reason_code,
        )
    
    def _on_message(self, client, userdata, message):
        """Callback when message received."""
        try:
            topic = message.topic
            
            # Decode payload
            try:
                payload = json.loads(message.payload.decode("utf-8"))
            except json.JSONDecodeError:
                # Some messages might not be JSON
                logger.debug(
                    "Non-JSON message received",
                    topic=topic,
                    payload_preview=message.payload[:100],
                )
                return
            
            self._message_count += 1
            self._last_message_time = datetime.utcnow()
            
            logger.debug(
                "Message received",
                topic=topic,
                payload_keys=list(payload.keys()) if isinstance(payload, dict) else type(payload).__name__,
            )
            
            # Call registered callback
            if self._message_callback and isinstance(payload, dict):
                self._message_callback(topic, payload)
                
        except Exception as e:
            self._error_count += 1
            logger.error(
                "Error processing message",
                topic=message.topic,
                error=str(e),
            )
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to broker."""
        return self._connected
    
    def get_stats(self) -> Dict[str, Any]:
        """Return client statistics."""
        return {
            "connected": self._connected,
            "broker": f"{settings.mqtt_broker_ip}:{settings.mqtt_port}",
            "topic": settings.mqtt_topic,
            "messages_received": self._message_count,
            "errors": self._error_count,
            "connected_since": self._connect_time.isoformat() if self._connect_time else None,
            "last_message": self._last_message_time.isoformat() if self._last_message_time else None,
        }
