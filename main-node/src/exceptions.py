"""
Exception classes and retry handler for the application.
"""

import time
import functools
from typing import Callable, TypeVar, Any
import asyncio
from .logger import setup_logger

logger = setup_logger(__name__)


class ApplicationError(Exception):
    """Base exception for application-specific errors."""
    pass


class DatabaseError(ApplicationError):
    """Raised when database operations fail."""
    pass


class FetchError(ApplicationError):
    """Raised when API fetch operations fail."""
    pass


class RetryExhausted(ApplicationError):
    """Raised when all retry attempts are exhausted."""
    pass


# Track consecutive errors for the final escalation
consecutive_errors: dict[str, int] = {}
ERROR_ESCALATION_THRESHOLD = 5


def track_error(operation_name: str) -> int:
    """
    Track consecutive errors for a given operation.
    Returns the current error count.
    """
    consecutive_errors[operation_name] = consecutive_errors.get(operation_name, 0) + 1
    return consecutive_errors[operation_name]


def reset_error(operation_name: str) -> None:
    """Reset error counter for a successful operation."""
    consecutive_errors[operation_name] = 0


F = TypeVar('F', bound=Callable[..., Any])


def retry_with_backoff(
    max_attempts: int | None = None,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    operation_name: str | None = None
) -> Callable[[F], F]:
    """
    Decorator to retry a function with exponential backoff.
    
    Args:
        max_attempts: Max retry attempts (if None, uses settings.RETRY_ATTEMPTS)
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        backoff_factor: Multiplier for exponential backoff
        operation_name: Name for logging/tracking (defaults to function name)
    
    Raises:
        RetryExhausted: When all retries are exhausted
    """
    from .config import settings
    
    max_retries = max_attempts or settings.RETRY_ATTEMPTS
    
    def decorator(func: F) -> F:
        op_name = operation_name or func.__name__

        @functools.wraps(func)
        def _sync_wrapper(*args, **kwargs):
            attempt = 0
            delay = base_delay

            while attempt < max_retries:
                try:
                    result = func(*args, **kwargs)
                    reset_error(op_name)
                    return result

                except Exception as e:
                    attempt += 1
                    error_count = track_error(op_name)

                    if attempt >= max_retries:
                        logger.error(
                            f"Retry exhausted for '{op_name}' after {max_retries} attempts: {e}",
                            exc_info=True
                        )

                        if error_count >= ERROR_ESCALATION_THRESHOLD:
                            logger.critical(
                                f"ESCALATION: '{op_name}' failed {error_count} times consecutively. "
                                "Switching to 1-minute retry interval."
                            )

                        raise RetryExhausted(
                            f"Failed after {max_retries} attempts: {e}"
                        ) from e

                    actual_delay = min(delay, max_delay)
                    logger.warning(
                        f"Attempt {attempt}/{max_retries} for '{op_name}' failed: {e}. "
                        f"Retrying in {actual_delay:.1f}s..."
                    )

                    time.sleep(actual_delay)
                    delay *= backoff_factor

        @functools.wraps(func)
        async def _async_wrapper(*args, **kwargs):
            attempt = 0
            delay = base_delay

            while attempt < max_retries:
                try:
                    result = await func(*args, **kwargs)
                    reset_error(op_name)
                    return result

                except Exception as e:
                    attempt += 1
                    error_count = track_error(op_name)

                    if attempt >= max_retries:
                        logger.error(
                            f"Retry exhausted for '{op_name}' after {max_retries} attempts: {e}",
                            exc_info=True
                        )

                        if error_count >= ERROR_ESCALATION_THRESHOLD:
                            logger.critical(
                                f"ESCALATION: '{op_name}' failed {error_count} times consecutively. "
                                "Switching to 1-minute retry interval."
                            )

                        raise RetryExhausted(
                            f"Failed after {max_retries} attempts: {e}"
                        ) from e

                    actual_delay = min(delay, max_delay)
                    logger.warning(
                        f"Attempt {attempt}/{max_retries} for '{op_name}' failed: {e}. "
                        f"Retrying in {actual_delay:.1f}s..."
                    )

                    await asyncio.sleep(actual_delay)
                    delay *= backoff_factor

        # Return async wrapper if the function is a coroutine function
        if asyncio.iscoroutinefunction(func):
            return _async_wrapper  # type: ignore

        return _sync_wrapper  # type: ignore
    
    return decorator
