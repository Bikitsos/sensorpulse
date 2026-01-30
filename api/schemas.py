# ================================
# SensorPulse API - Pydantic Schemas
# ================================

from datetime import datetime, time
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr


# ================================
# Sensor Schemas
# ================================

class SensorReadingBase(BaseModel):
    """Base schema for sensor readings."""
    topic: str
    device_name: str
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    battery: Optional[int] = None
    linkquality: Optional[int] = None


class SensorReading(SensorReadingBase):
    """Full sensor reading with timestamp and raw data."""
    time: datetime
    raw_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class SensorLatest(SensorReadingBase):
    """Latest reading for a sensor (used in dashboard cards)."""
    time: datetime
    last_seen_minutes: Optional[int] = None

    class Config:
        from_attributes = True


class DeviceInfo(BaseModel):
    """Device/sensor information."""
    topic: str
    device_name: str
    last_seen: datetime
    reading_count: int = 0
    
    class Config:
        from_attributes = True


class HistoryQuery(BaseModel):
    """Query parameters for history endpoint."""
    hours: int = Field(default=24, ge=1, le=168)  # Max 7 days
    resolution: Optional[str] = Field(default=None, pattern="^(1m|5m|15m|1h)$")


class SensorHistory(BaseModel):
    """Historical data for a sensor."""
    device_name: str
    topic: str
    readings: List[SensorReading]
    summary: Optional["HistorySummary"] = None


class HistorySummary(BaseModel):
    """Summary statistics for historical data."""
    min_temp: Optional[float] = None
    max_temp: Optional[float] = None
    avg_temp: Optional[float] = None
    min_humidity: Optional[float] = None
    max_humidity: Optional[float] = None
    avg_humidity: Optional[float] = None
    reading_count: int = 0


# ================================
# User Schemas
# ================================

class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    name: Optional[str] = None
    picture: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a user."""
    pass


class User(UserBase):
    """Full user schema."""
    id: UUID
    is_allowed: bool = False
    daily_report: bool = False
    report_time: Optional[time] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserPreferences(BaseModel):
    """User preferences update schema."""
    daily_report: Optional[bool] = None
    report_time: Optional[time] = None


# ================================
# Auth Schemas
# ================================

class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Decoded JWT token data."""
    user_id: str
    email: str
    exp: datetime


class GoogleUser(BaseModel):
    """User info from Google OAuth."""
    id: str
    email: EmailStr
    name: Optional[str] = None
    picture: Optional[str] = None


# ================================
# Report Schemas
# ================================

class ReportSummary(BaseModel):
    """Daily report summary for a sensor."""
    device_name: str
    min_temp: Optional[float] = None
    max_temp: Optional[float] = None
    avg_temp: Optional[float] = None
    min_humidity: Optional[float] = None
    max_humidity: Optional[float] = None
    avg_humidity: Optional[float] = None
    battery: Optional[int] = None
    last_seen: datetime
    is_offline: bool = False


class DailyReport(BaseModel):
    """Full daily report."""
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    sensors: List[ReportSummary]
    alerts: List[str] = []


# ================================
# API Response Schemas
# ================================

class HealthCheck(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    version: str
    database: str


class APIError(BaseModel):
    """API error response."""
    detail: str
    code: Optional[str] = None


# Update forward references
SensorHistory.model_rebuild()
