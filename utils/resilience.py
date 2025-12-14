"""
Resilience Utilities
Provides decorators and helpers for retry logic and potential failure recovery.
"""
import asyncio
import logging
from functools import wraps
from typing import Type, Tuple, Optional, Callable
import time
import requests
import httpx

from config.settings import settings
from config.logger_config import setup_logger

logger = setup_logger("Resilience", settings.LOG_LEVEL)

def retry_with_backoff(
    retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator to retry async or sync functions with exponential backoff.
    
    Args:
        retries: Maximum number of retries.
        initial_delay: Initial delay in seconds.
        max_delay: Maximum delay in seconds.
        backoff_factor: Multiplier for delay after each failure.
        exceptions: Exceptions to catch and retry on.
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == retries:
                        logger.error(f"❌ {func.__name__} failed after {retries} retries: {e}")
                        raise
                    
                    logger.warning(f"⚠️ {func.__name__} failed (Attempt {attempt+1}/{retries}): {e}")
                    logger.info(f"⏳ Waiting {delay:.1f}s before retry...")
                    await asyncio.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == retries:
                        logger.error(f"❌ {func.__name__} failed after {retries} retries: {e}")
                        raise
                    
                    logger.warning(f"⚠️ {func.__name__} failed (Attempt {attempt+1}/{retries}): {e}")
                    logger.info(f"⏳ Waiting {delay:.1f}s before retry...")
                    time.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

# Common exceptions to retry on for Network calls
NETWORK_EXCEPTIONS = (
    requests.exceptions.RequestException,
    httpx.RequestError,
    httpx.ConnectError,
    httpx.TimeoutException,
    TimeoutError,
    ConnectionError,
    asyncio.TimeoutError
)
