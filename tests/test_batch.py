"""Tests for batch processing module"""
import pytest
from pdf_trans_tools.batch import BatchProcessor, BatchResult


class TestBatch:
    """Test cases for BatchProcessor."""

    def test_batch_processor_init(self):
        """Test BatchProcessor initialization."""
        processor = BatchProcessor()
        assert processor.max_workers == 4

    def test_batch_processor_init_custom_workers(self):
        """Test BatchProcessor with custom workers."""
        processor = BatchProcessor(max_workers=8)
        assert processor.max_workers == 8

    def test_batch_result_dataclass(self):
        """Test BatchResult dataclass."""
        result = BatchResult(
            total=10,
            succeeded=8,
            failed=2,
            results=[("file1.pdf", True, None), ("file2.pdf", False, "Error")]
        )
        assert result.total == 10
        assert result.succeeded == 8
        assert result.failed == 2
        assert len(result.results) == 2
