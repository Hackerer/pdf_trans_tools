"""Tests for retry module"""
import time
import pytest
from pdf_trans_tools.retry import with_retry, RetryExhaustedError, RetryStats, get_retry_stats


class TestRetry:
    """Test cases for retry functionality."""

    def test_retry_success_first_try(self):
        """Test retry decorator succeeds on first try."""
        @with_retry(max_attempts=3)
        def successful_func():
            return "success"

        result = successful_func()
        assert result == "success"

    def test_retry_success_after_failure(self):
        """Test retry decorator succeeds after initial failure."""
        call_count = 0

        @with_retry(max_attempts=3, base_delay=0.1)
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary error")
            return "success"

        result = flaky_func()
        assert result == "success"
        assert call_count == 2

    def test_retry_exhausted(self):
        """Test retry decorator raises RetryExhaustedError after all attempts fail."""
        @with_retry(max_attempts=3, base_delay=0.1)
        def always_fails():
            raise ValueError("Permanent error")

        with pytest.raises(RetryExhaustedError) as exc_info:
            always_fails()
        assert "Failed after 3 attempts" in str(exc_info.value)

    def test_retry_stats(self):
        """Test RetryStats tracking."""
        stats = RetryStats()
        stats.record_success(used_retry=False)
        stats.record_success(used_retry=True)
        stats.record_exhausted()

        result = stats.get_stats()
        assert result["total_calls"] == 3
        assert result["succeeded_first_try"] == 1
        assert result["retried"] == 1
        assert result["exhausted"] == 1
        assert result["success_rate"] == 2/3

    def test_get_retry_stats(self):
        """Test global retry stats getter."""
        stats = get_retry_stats()
        assert isinstance(stats, RetryStats)
