"""
pdf_trans_tools retry - Retry logic for transient failures
"""
import logging
import time
from functools import wraps
from typing import Callable, Type, Tuple

logger = logging.getLogger(__name__)


class RetryExhaustedError(Exception):
    """Raised when all retry attempts are exhausted."""
    pass


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator to add retry logic with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exponential_base: Base for exponential backoff calculation
        exceptions: Tuple of exception types to catch and retry

    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(f"Retry exhausted after {max_attempts} attempts: {e}")
                        raise RetryExhaustedError(
                            f"Failed after {max_attempts} attempts: {e}"
                        ) from e

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** (attempt - 1)), max_delay)
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)

            # Should not reach here, but just in case
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


class RetryStats:
    """Track retry statistics."""

    def __init__(self):
        self.total_calls = 0
        self.succeeded_first_try = 0
        self.retried = 0
        self.exhausted = 0

    def record_success(self, used_retry: bool = False):
        """Record a successful call."""
        self.total_calls += 1
        if used_retry:
            self.retried += 1
        else:
            self.succeeded_first_try += 1

    def record_exhausted(self):
        """Record a call that exhausted all retries."""
        self.total_calls += 1
        self.exhausted += 1

    def get_stats(self) -> dict:
        """Get retry statistics."""
        return {
            "total_calls": self.total_calls,
            "succeeded_first_try": self.succeeded_first_try,
            "retried": self.retried,
            "exhausted": self.exhausted,
            "success_rate": (
                (self.total_calls - self.exhausted) / self.total_calls
                if self.total_calls > 0 else 0.0
            )
        }


# Global retry stats
_global_retry_stats = RetryStats()


def get_retry_stats() -> RetryStats:
    """Get the global retry statistics tracker."""
    return _global_retry_stats
