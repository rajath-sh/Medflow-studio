"""
HealthOps Studio -- Middleware Stack

All middleware classes for the FastAPI application:
1. SecurityHeadersMiddleware -- Adds browser security headers
2. CorrelationIdMiddleware -- Tags each request with a unique ID for tracing
3. RateLimitMiddleware -- Prevents abuse via request throttling
4. RequestLoggingMiddleware -- Structured JSON logging for every request

These run on EVERY request, wrapping the entire application.
"""

import uuid
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from app.logging_config import get_logger

logger = get_logger("healthops.request")


# ── 1. Security Headers ──────────────────────────────────

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds browser security headers to every response.

    WHY EACH HEADER:
    - X-Content-Type-Options: Prevents browser from guessing MIME types (prevents XSS)
    - X-Frame-Options: Prevents clickjacking by blocking iframes
    - X-XSS-Protection: Legacy XSS filter (for older browsers)
    - Referrer-Policy: Controls how much URL info is sent in Referer header
    - Permissions-Policy: Disables camera/mic/geolocation access
    - Cache-Control: Prevents sensitive API responses from being cached
    - Strict-Transport-Security: Forces HTTPS (only effective over HTTPS)
    """
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"

        # HSTS -- only add if running over HTTPS
        # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response


# ── 2. Correlation ID ─────────────────────────────────────

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Assigns a unique ID to each request for distributed tracing.

    The X-Request-ID header is:
    - Generated if not present in the incoming request
    - Passed through if the client sends one (e.g., from a load balancer)
    - Included in the response for debugging
    """
    async def dispatch(self, request: Request, call_next):
        # Use client-provided ID or generate a new one
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Store in request state so route handlers can access it
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response


# ── 3. Rate Limiting ──────────────────────────────────────

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory sliding window rate limiter.

    Limits:
    - 100 requests per minute per IP (general)
    - 10 requests per minute for /auth/* endpoints (login brute-force protection)
    - 20 requests per minute for /ai/* endpoints (expensive operations)

    NOTE: For production, replace with Redis-based rate limiting.
    This in-memory version works for single-instance deployments.
    """

    def __init__(self, app):
        super().__init__(app)
        self._requests: dict[str, list[float]] = {}
        # path_prefix -> (max_requests, window_seconds)
        self._limits = {
            "/auth/": (10, 60),
            "/ai/": (20, 60),
        }
        self._default_limit = (100, 60)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        now = time.time()

        # Determine which limit applies
        limit, window = self._default_limit
        for prefix, (lim, win) in self._limits.items():
            if path.startswith(prefix):
                limit, window = lim, win
                break

        # Key: IP + path_prefix for granular limiting
        key = f"{client_ip}:{path.split('/')[1] if '/' in path[1:] else 'root'}"

        # Clean old entries + check count
        if key not in self._requests:
            self._requests[key] = []

        # Remove expired timestamps
        self._requests[key] = [t for t in self._requests[key] if now - t < window]

        if len(self._requests[key]) >= limit:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"Rate limit exceeded. Max {limit} requests per {window}s.",
                    "retry_after": window,
                },
                headers={"Retry-After": str(window)},
            )

        self._requests[key].append(now)

        return await call_next(request)


# ── 4. Request Logging ───────────────────────────────────

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every HTTP request with structured JSON data.

    Captures: method, route, status_code, latency_ms, client_ip, request_id.
    Skips health-check endpoints to reduce noise.
    """

    SKIP_PATHS = {"/docs", "/openapi.json", "/redoc", "/favicon.ico"}

    async def dispatch(self, request: Request, call_next):
        # Skip noisy endpoints
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        start = time.time()
        response = await call_next(request)
        latency_ms = round((time.time() - start) * 1000, 2)

        # Get request context
        request_id = getattr(request.state, "request_id", "unknown")
        client_ip = request.client.host if request.client else "unknown"
        user_id = getattr(request.state, "user_id", None)

        log_data = {
            "request_id": request_id,
            "client_ip": client_ip,
            "method": request.method,
            "route": request.url.path,
            "status_code": response.status_code,
            "latency_ms": latency_ms,
        }
        if user_id:
            log_data["user_id"] = str(user_id)

        # Log level based on status code
        if response.status_code >= 500:
            logger.error("Request failed", extra=log_data)
        elif response.status_code >= 400:
            logger.warning("Client error", extra=log_data)
        else:
            logger.info("Request completed", extra=log_data)

        return response
