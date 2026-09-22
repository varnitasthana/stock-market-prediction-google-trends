"""
Rate limiting middleware for FastAPI

NOTE: This implementation uses in-memory storage (defaultdict) which means:
- Rate limits are per-worker, not shared across multiple workers
- Rate limits reset when the application restarts
- Suitable for local development and single-worker deployments
- NOT suitable for distributed/multi-worker production environments

For production with multiple workers, consider using Redis-backed rate limiting
such as slowapi or a similar library that shares state across workers.
"""
import time
from collections import defaultdict
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, calls: int = 60, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        
        # Skip rate limiting for health checks
        if request.url.path == "/api/health":
            return await call_next(request)
        
        now = time.time()
        
        # Clean old entries
        self.clients[client_ip] = [
            timestamp for timestamp in self.clients[client_ip]
            if now - timestamp < self.period
        ]
        
        # Check rate limit
        if len(self.clients[client_ip]) >= self.calls:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"Rate limit exceeded. Maximum {self.calls} requests per {self.period} seconds."
                },
                headers={"Retry-After": str(self.period)}
            )
        
        # Add current request
        self.clients[client_ip].append(now)
        
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(self.calls - len(self.clients[client_ip]))
        response.headers["X-RateLimit-Reset"] = str(int(now + self.period))
        
        return response
