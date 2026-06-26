"""
Security Headers and Request Logging Middleware

Injects essential security headers into all responses and logs all requests
with timing info using structured logs.
"""

import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from backend.core.config import settings
from backend.core.logging import get_logger

logger = get_logger("backend.middleware")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Enforces security best-practices by appending essential OWASP headers
    to every outbound HTTP response.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # 1. Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # 2. Prevent MIME-sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # 3. Enable browser XSS filtering
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # 4. Strict Transport Security (HSTS) - Enforced in production only
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # 5. Content Security Policy (CSP) - restrict resource loads
        # Relaxed standard for API docs (/docs, /redoc) to fetch CSS/JS assets
        if request.url.path.startswith(("/docs", "/redoc")):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https://fastapi.tiangolo.com;"
            )
        else:
            response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"

        # 6. Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Structured HTTP Request & Response logger.
    Captures method, URI, duration, and response status codes.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        
        # Log request receipt
        logger.debug(
            "http_request_received",
            method=request.method,
            path=request.url.path,
            ip=request.client.host if request.client else "unknown",
        )

        try:
            response = await call_next(request)
            duration = time.perf_counter() - start_time
            
            logger.info(
                "http_request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2),
            )
            return response
            
        except Exception as e:
            duration = time.perf_counter() - start_time
            logger.error(
                "http_request_failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                duration_ms=round(duration * 1000, 2),
            )
            raise e
