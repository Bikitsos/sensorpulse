# ================================
# SensorPulse Ingester - Health Check Server
# ================================

import asyncio
from datetime import datetime
from typing import Dict, Any, Callable
from aiohttp import web

from config import settings
from logger import logger


class HealthServer:
    """
    HTTP server for health checks and metrics.
    
    Endpoints:
    - GET /health - Health check for container orchestration
    - GET /metrics - Detailed metrics for monitoring
    - GET /ready - Readiness probe
    """
    
    def __init__(self):
        self.app = web.Application()
        self.runner: web.AppRunner = None
        self._stats_callback: Callable[[], Dict[str, Any]] = lambda: {}
        self._start_time = datetime.utcnow()
        
        # Register routes
        self.app.router.add_get("/health", self._health_handler)
        self.app.router.add_get("/metrics", self._metrics_handler)
        self.app.router.add_get("/ready", self._ready_handler)
        self.app.router.add_get("/", self._root_handler)
    
    def set_stats_callback(self, callback: Callable[[], Dict[str, Any]]):
        """Set callback to retrieve current statistics."""
        self._stats_callback = callback
    
    async def start(self):
        """Start the health check server."""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        site = web.TCPSite(
            self.runner,
            settings.health_host,
            settings.health_port,
        )
        
        await site.start()
        logger.info(
            "Health server started",
            host=settings.health_host,
            port=settings.health_port,
        )
    
    async def stop(self):
        """Stop the health check server."""
        if self.runner:
            await self.runner.cleanup()
            logger.info("Health server stopped")
    
    async def _root_handler(self, request: web.Request) -> web.Response:
        """Root endpoint with service info."""
        return web.json_response({
            "service": "sensorpulse-ingester",
            "version": "0.1.0",
            "endpoints": ["/health", "/metrics", "/ready"],
        })
    
    async def _health_handler(self, request: web.Request) -> web.Response:
        """
        Health check endpoint.
        
        Returns 200 if service is running, 503 otherwise.
        """
        stats = self._stats_callback()
        
        # Determine health status
        mqtt_ok = stats.get("mqtt", {}).get("connected", False)
        db_ok = stats.get("database", {}).get("connected", False)
        
        is_healthy = mqtt_ok and db_ok
        
        response = {
            "status": "healthy" if is_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "mqtt": "ok" if mqtt_ok else "fail",
                "database": "ok" if db_ok else "fail",
            },
        }
        
        status_code = 200 if is_healthy else 503
        return web.json_response(response, status=status_code)
    
    async def _ready_handler(self, request: web.Request) -> web.Response:
        """
        Readiness probe endpoint.
        
        Returns 200 if service is ready to receive traffic.
        """
        stats = self._stats_callback()
        
        mqtt_ok = stats.get("mqtt", {}).get("connected", False)
        db_ok = stats.get("database", {}).get("connected", False)
        
        is_ready = mqtt_ok and db_ok
        
        if is_ready:
            return web.json_response({"ready": True})
        else:
            return web.json_response(
                {"ready": False, "reason": "Dependencies not ready"},
                status=503,
            )
    
    async def _metrics_handler(self, request: web.Request) -> web.Response:
        """
        Detailed metrics endpoint.
        
        Returns comprehensive statistics about the ingester.
        """
        stats = self._stats_callback()
        
        uptime = (datetime.utcnow() - self._start_time).total_seconds()
        
        response = {
            "service": "sensorpulse-ingester",
            "version": "0.1.0",
            "uptime_seconds": uptime,
            "timestamp": datetime.utcnow().isoformat(),
            **stats,
        }
        
        return web.json_response(response)
