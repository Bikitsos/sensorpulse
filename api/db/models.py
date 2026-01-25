# ================================
# SensorPulse - Database Models
# ================================

import uuid
from datetime import datetime, time
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Boolean,
    DateTime,
    Time,
    Text,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.sql import func

from .database import Base


class SensorReading(Base):
    """
    Stores sensor readings from Zigbee2MQTT devices.
    
    Designed to handle variable payloads - common fields are extracted
    for efficient querying, while raw_data preserves the full payload.
    """
    __tablename__ = "sensor_readings"

    # Composite primary key: time + topic for time-series data
    time = Column(
        TIMESTAMP(timezone=True),
        primary_key=True,
        default=func.now(),
        nullable=False,
    )
    topic = Column(
        Text,
        primary_key=True,
        nullable=False,
        index=True,
    )
    
    # Common sensor fields (nullable for different device types)
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    battery = Column(Integer, nullable=True)
    linkquality = Column(Integer, nullable=True)
    
    # Store full payload for flexibility
    raw_data = Column(JSONB, nullable=True)

    # Indexes for common query patterns
    __table_args__ = (
        Index("ix_sensor_readings_time", "time"),
        Index("ix_sensor_readings_topic_time", "topic", "time"),
    )

    def __repr__(self):
        return f"<SensorReading(topic={self.topic}, time={self.time}, temp={self.temperature})>"


class User(Base):
    """
    User accounts authenticated via Google OAuth.
    
    Only whitelisted users (is_allowed=True) can access the dashboard.
    """
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=True)
    picture = Column(Text, nullable=True)
    
    # Access control
    is_allowed = Column(Boolean, default=False, nullable=False)
    
    # Daily report preferences
    daily_report = Column(Boolean, default=False, nullable=False)
    report_time = Column(Time, default=time(8, 0), nullable=True)  # Default 8:00 AM
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
    )

    def __repr__(self):
        return f"<User(email={self.email}, allowed={self.is_allowed})>"
