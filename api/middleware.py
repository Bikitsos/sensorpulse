# ================================
# SensorPulse API - Rate Limiting Middleware
# ================================

import time
from typing import Dict, Tuple
from collections import defaultdict
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from config import settings


class RateLimiter:
    """
    Simple in-memory rate limiter using sliding window.
    
    For production, consider using Redis-based rate limiting.
    """
    
    def __init__(self, requests_per_minute: int = 100):
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # seconds
        self._requests: Dict[str, list] = defaultdict(list)
    
    def _get_client_key(self, request: Request) -> str:
        """Get unique key for the client (IP or user ID)."""
        # Try to get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"
        
        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"
    
    def _cleanup_old_requests(self, key: str, now: float):
        """Remove requests outside the sliding window."""
        cutoff = now - self.window_size
        self._requests[key] = [
            t for t in self._requests[key] if t > cutoff
        ]
    
    def is_allowed(self, request: Request) -> Tuple[bool, Dict]:
        """
        Check if request is allowed under rate limit.
        
        Returns (allowed, headers) where headers contains rate limit info.
        """
        key = self._get_client_key(request)
        now = time.time()
        
        # Cleanup old requests
        self._cleanup_old_requests(key, now)
        
        # Check rate limit
        request_count = len(self._requests[key])
        remaining = max(0, self.requests_per_minute - request_count)
        reset_time = int(now + self.window_size)
        
        headers = {
            "X-RateLimit-Limit": str(self.requests_per_minute),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time),
        }
        
        if request_count >= self.requests_per_minute:
            headers["Retry-After"] = str(self.window_size)
            return False, headers
        
        # Record this request
        self._requests[key].append(now)
        headers["X-RateLimit-Remaining"] = str(remaining - 1)
        
        return True, headers


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""
    
    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.limiter = RateLimiter(requests_per_minute)
        
        # Paths to exclude from rate limiting
        self.excluded_paths = {
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/ws/sensors",  # WebSockets handle their own limits
        }
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        # Check rate limit
        allowed, headers = self.limiter.is_allowed(request)
        
        if not allowed:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Try again later."},
                headers=headers,
            )
        
        # Process request and add rate limit headers to response
        response = await call_next(request)
        
        for key, value in headers.items():
            response.headers[key] = value
        
        return response


# Global rate limiter instance
rate_limiter = RateLimiter(settings.rate_limit_per_minute)
