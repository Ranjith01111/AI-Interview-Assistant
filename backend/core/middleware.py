"""
Security Headers and Request Logging Middleware

Injects essential security headers into all responses and logs all requests
with timing info using structured logs.
"""

import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.responses import JSONResponse

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
    Includes Payload Sniffing to capture exact request details on failure.
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
                sniffed_payload="<payload sniffing disabled>",
                sniffed_headers=dict(request.headers)
            )
            raise e


class RequestBodySizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Rejects requests with Content-Length exceeding the configured max body size.
    Protects against oversized payloads exhausting memory.
    
    Default: 5MB (covers resume uploads up to 10MB file + multipart overhead).
    """
    def __init__(self, app, max_body_size: int = 5 * 1024 * 1024):
        super().__init__(app)
        self.max_body_size = max_body_size

    async def dispatch(self, request: Request, call_next) -> Response:
        # Check Content-Length header if present
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.max_body_size:
                    return JSONResponse(
                        status_code=413,
                        content={"detail": f"Request body too large. Maximum size is {self.max_body_size // (1024*1024)}MB."}
                    )
            except ValueError:
                pass  # Invalid header — let downstream handle it

        return await call_next(request)
