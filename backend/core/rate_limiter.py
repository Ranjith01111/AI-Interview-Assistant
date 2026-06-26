"""
Rate Limiter Configuration

Initializes and configures the slowapi rate limiter.
Uses the client's IP address (get_remote_address) as the rate limiting key.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from backend.core.config import settings

# Create a single Limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.RATE_LIMIT_DEFAULT],
)
