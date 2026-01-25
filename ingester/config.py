# ================================
# SensorPulse Ingester - Configuration
# ================================

import os
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    
    # MQTT Broker Configuration
    mqtt_broker_ip: str = Field(
        default="192.168.1.100",
        description="External MQTT broker IP address"
    )
    mqtt_port: int = Field(
        default=1883,
        description="MQTT broker port"
    )
    mqtt_user: str = Field(
        default="",
        description="MQTT username (optional)"
    )
    mqtt_pass: str = Field(
        default="",
        description="MQTT password (optional)"
    )
    mqtt_topic: str = Field(
        default="zigbee2mqtt/+",
        description="MQTT topic to subscribe to (supports wildcards)"
    )
    mqtt_client_id: str = Field(
        default="sensorpulse_ingester",
        description="MQTT client identifier"
    )
    mqtt_reconnect_delay: int = Field(
        default=5,
        description="Seconds to wait before reconnecting"
    )
    
    # Database Configuration
    database_url: str = Field(
        default="postgresql://sensorpulse:changeme@db:5432/sensorpulse",
        description="PostgreSQL connection string"
    )
    db_pool_size: int = Field(
        default=5,
        description="Database connection pool size"
    )
    
    # Health Check Server
    health_host: str = Field(
        default="0.0.0.0",
        description="Health check server host"
    )
    health_port: int = Field(
        default=8001,
        description="Health check server port"
    )
    
    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
    log_format: str = Field(
        default="json",
        description="Log format (json or text)"
    )
    
    # Processing
    batch_size: int = Field(
        default=100,
        description="Number of messages to batch before writing"
    )
    batch_timeout: float = Field(
        default=5.0,
        description="Seconds to wait before flushing partial batch"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
