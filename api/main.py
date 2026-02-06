# ================================
# SensorPulse API - Main Application
# ================================

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from db import engine
from middleware import RateLimitMiddleware
from routes import sensors, auth, websocket, reports
from websocket import ws_manager
from cleanup import cleanup_scheduler, cleanup_old_readings

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    logger.info(
        "SensorPulse API starting",
        version=settings.version,
        environment="development" if settings.debug else "production",
    )
    
    # Test database connection
    try:
        from db import test_connection
        await test_connection()
        logger.info("Database connection established")
    except Exception as e:
        logger.error("Database connection failed", error=str(e))
        raise
    
    # Start background data cleanup scheduler
    cleanup_task = asyncio.create_task(cleanup_scheduler())
    logger.info("Data cleanup scheduler launched")
    
    yield
    
    # Shutdown
    logger.info("SensorPulse API shutting down")
    
    # Cancel cleanup scheduler
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    
    # Close all WebSocket connections
    await ws_manager.disconnect_all()
    
    # Dispose database engine
    await engine.dispose()
    
    logger.info("SensorPulse API shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="SensorPulse API",
    description="""
    🌡️ **SensorPulse** - Real-time sensor monitoring dashboard API
    
    ## Features
    
    - **Real-time Updates**: WebSocket support for live sensor data
    - **Historical Data**: Query sensor history with flexible time ranges
    - **Daily Reports**: Automated email reports with sensor summaries
    - **Multi-device**: Support for multiple Zigbee2MQTT sensors
    
    ## Authentication
    
    This API uses Google OAuth 2.0 for authentication. 
    Start the flow at `/auth/login` to get an access token.
    
    ## WebSocket
    
    Connect to `/ws/sensors` for real-time sensor updates.
    Send `{"action": "subscribe", "device": "sensor_name"}` to subscribe.
    """,
    version=settings.version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan,
)


# ================================
# Middleware Configuration
# ================================

# CORS Middleware - Must be added first
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
)

# Rate Limiting Middleware
app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.rate_limit_per_minute)


# ================================
# Global Exception Handlers
# ================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.error(
        "Unhandled exception",
        path=str(request.url.path),
        method=request.method,
        error=str(exc),
        exc_info=True,
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "code": "INTERNAL_ERROR",
        },
    )


# ================================
# Include Routers
# ================================

app.include_router(sensors.router)
app.include_router(auth.router)
app.include_router(reports.router)
app.include_router(websocket.router)


# ================================
# Health Check Endpoint
# ================================

@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint for container orchestration.
    
    Returns basic health status and version information.
    """
    db_status = "unknown"
    
    try:
        from db import test_connection
        await test_connection()
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.version,
        "database": db_status,
    }


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint - redirect to docs or return API info."""
    return {
        "name": "SensorPulse API",
        "version": settings.version,
        "docs": "/docs" if settings.debug else None,
        "health": "/health",
    }


@app.post("/api/admin/cleanup", tags=["admin"])
async def trigger_cleanup(days: int = 30):
    """
    Manually trigger data cleanup.
    
    Deletes sensor readings older than the specified number of days.
    Default retention: 30 days.
    """
    deleted = await cleanup_old_readings(retention_days=days)
    return {
        "status": "completed",
        "rows_deleted": deleted,
        "retention_days": days,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ================================
# Development Server
# ================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )
