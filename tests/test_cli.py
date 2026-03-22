"""Tests for CLI module"""
import pytest
from pdf_trans_tools import cli


class TestCLI:
    """Test cases for CLI module."""

    def test_setup_logging_exists(self):
        """Test setup_logging function exists."""
        assert hasattr(cli, 'setup_logging')
        assert callable(cli.setup_logging)

    def test_translate_single_exists(self):
        """Test translate_single function exists."""
        assert hasattr(cli, 'translate_single')
        assert callable(cli.translate_single)

    def test_translate_batch_exists(self):
        """Test translate_batch function exists."""
        assert hasattr(cli, 'translate_batch')
        assert callable(cli.translate_batch)

    def test_main_exists(self):
        """Test main function exists."""
        assert hasattr(cli, 'main')
        assert callable(cli.main)
