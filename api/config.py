# ================================
# SensorPulse API - Configuration
# ================================

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    
    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://sensorpulse:changeme@db:5432/sensorpulse",
        description="PostgreSQL async connection string"
    )
    
    # API Server
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_debug: bool = Field(default=False)
    
    # Security
    secret_key: str = Field(
        default="changeme_generate_a_secure_random_string",
        description="Secret key for JWT signing"
    )
    jwt_algorithm: str = Field(default="HS256")
    jwt_expire_minutes: int = Field(default=60 * 24 * 7)  # 7 days
    
    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins"
    )
    
    # Google OAuth
    google_client_id: str = Field(default="")
    google_client_secret: str = Field(default="")
    oauth_redirect_uri: str = Field(default="http://localhost:8000/auth/callback")
    
    # Email Reports (Resend)
    resend_api_key: str = Field(default="")
    email_from: str = Field(default="noreply@sensorpulse.local")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=100)
    
    # App Info
    app_version: str = Field(default="0.1.0")
    app_name: str = Field(default="SensorPulse API")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
