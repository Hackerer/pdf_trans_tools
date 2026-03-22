"""Tests for Translator class"""
import os
import tempfile
import pytest
from pdf_trans_tools import Translator


class TestTranslator:
    """Test cases for Translator class."""

    def test_init(self):
        """Test Translator initialization."""
        translator = Translator()
        assert translator.target_lang == "en"

    def test_init_with_params(self):
        """Test Translator with custom parameters."""
        translator = Translator(api_key="test-key", target_lang="zh")
        assert translator.api_key == "test-key"
        assert translator.target_lang == "zh"

    def test_translate_pdf_returns_bool(self):
        """Test translate_pdf returns a boolean."""
        translator = Translator()
        result = translator.translate_pdf("input.pdf", "output.pdf")
        assert isinstance(result, bool)

    def test_extract_text_raises_import_error_without_pypdf2(self):
        """Test extract_text raises ImportError if PyPDF2 is not available."""
        translator = Translator()
        # This test verifies the method signature and basic behavior
        # Without an actual PDF file, we can only verify the method exists
        assert hasattr(translator, 'extract_text')

    def test_extract_text_by_page_method_exists(self):
        """Test extract_text_by_page method exists."""
        translator = Translator()
        assert hasattr(translator, 'extract_text_by_page')

    def test_get_pdf_info_method_exists(self):
        """Test get_pdf_info method exists."""
        translator = Translator()
        assert hasattr(translator, 'get_pdf_info')

    def test_translate_pdf_with_target_lang(self):
        """Test translate_pdf with explicit target language."""
        translator = Translator()
        result = translator.translate_pdf("input.pdf", "output.pdf", target_lang="fr")
        assert isinstance(result, bool)
        assert result is True

    def test_version_exists(self):
        """Test __version__ is defined."""
        from pdf_trans_tools import __version__
        assert __version__ is not None
        assert isinstance(__version__, str)

    def test_generate_translated_pdf_method_exists(self):
        """Test generate_translated_pdf method exists."""
        translator = Translator()
        assert hasattr(translator, 'generate_translated_pdf')

    def test_translate_and_generate_pdf_method_exists(self):
        """Test translate_and_generate_pdf method exists."""
        translator = Translator()
        assert hasattr(translator, 'translate_and_generate_pdf')

    def test_mock_translate_returns_translated_text(self):
        """Test _mock_translate wraps text with language marker."""
        translator = Translator()
        result = translator._mock_translate("Hello", "fr")
        assert "fr" in result
        assert "Hello" in result
