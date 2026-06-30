"""
Resilience Utilities

Provides decorators and tools for handling transient failures,
exponential backoff, and graceful degradation.
"""

import asyncio
import functools
import logging
from typing import Callable, Any, Type, Tuple, Optional

logger = logging.getLogger("backend.core.resilience")

class ServiceUnavailableError(Exception):
    """Raised when an external service or database is unreachable after retries."""
    def __init__(self, message: str = "Service unavailable", original_exception: Optional[Exception] = None):
        super().__init__(message)
        self.original_exception = original_exception


def retry_with_backoff(
    retries: int = 3,
    base_delay: float = 0.1,
    max_delay: float = 5.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator that retries an async function with exponential backoff.
    
    Args:
        retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay in seconds.
        exceptions: Tuple of exceptions that should trigger a retry.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = base_delay
            last_exception = None
            
            for attempt in range(retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == retries:
                        logger.error(
                            "retry_exhausted",
                            func=func.__name__,
                            retries=retries,
                            error=str(e)
                        )
                        break
                    
                    logger.warning(
                        "retry_attempt",
                        func=func.__name__,
                        attempt=attempt + 1,
                        delay_s=round(delay, 2),
                        error=str(e)
                    )
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, max_delay)
            
            # If we exhausted retries, raise ServiceUnavailableError
            raise ServiceUnavailableError(
                message=f"Service {func.__name__} unavailable after {retries} retries.",
                original_exception=last_exception
            ) from last_exception
            
        return wrapper
    return decorator
