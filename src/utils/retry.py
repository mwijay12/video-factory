# -*- coding: utf-8 -*-
import asyncio
import time
import random
import functools
from typing import Callable, Any, Tuple, Type, Union
import httpx
from loguru import logger

def calculate_delay(attempt: int, base_delay: float, max_delay: float) -> float:
    """Calculate exponential backoff delay with ±20% jitter."""
    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
    jitter = random.uniform(0.8, 1.2)
    return delay * jitter

def retry_async(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exceptions: Tuple[Type[BaseException], ...] = (
        httpx.HTTPError,
        httpx.TimeoutException,
        ConnectionError,
        asyncio.TimeoutError
    )
) -> Callable[..., Any]:
    """
    Async decorator that retries a function with exponential backoff and jitter.
    
    Usage:
        @retry_async(max_attempts=3, base_delay=1.0)
        async def fetch_data(url):
            ...
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.warning(
                            f"Async call {func.__name__} failed after {max_attempts} attempts. Error: {e}"
                        )
                        raise
                    
                    delay = calculate_delay(attempt, base_delay, max_delay)
                    logger.warning(
                        f"Async call {func.__name__} failed (attempt {attempt}/{max_attempts}). "
                        f"Retrying in {delay:.2f}s... Error: {e}"
                    )
                    await asyncio.sleep(delay)
            raise last_exception
        return wrapper
    return decorator

def retry_sync(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exceptions: Tuple[Type[BaseException], ...] = (
        httpx.HTTPError,
        httpx.TimeoutException,
        ConnectionError
    )
) -> Callable[..., Any]:
    """
    Sync decorator that retries a function with exponential backoff and jitter.
    
    Usage:
        @retry_sync(max_attempts=3, base_delay=1.0)
        def fetch_data_sync(url):
            ...
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.warning(
                            f"Sync call {func.__name__} failed after {max_attempts} attempts. Error: {e}"
                        )
                        raise
                    
                    delay = calculate_delay(attempt, base_delay, max_delay)
                    logger.warning(
                        f"Sync call {func.__name__} failed (attempt {attempt}/{max_attempts}). "
                        f"Retrying in {delay:.2f}s... Error: {e}"
                    )
                    time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator
