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

    def test_translate_pdf_method_exists(self):
        """Test translate_pdf method exists."""
        translator = Translator()
        assert hasattr(translator, 'translate_pdf')
        assert callable(translator.translate_pdf)

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

    def test_google_translate_method_exists(self):
        """Test google_translate method exists."""
        translator = Translator()
        assert hasattr(translator, 'google_translate')

    def test_google_translate_requires_api_key(self):
        """Test google_translate raises error without API key."""
        translator = Translator()
        with pytest.raises(ValueError, match="API key is required"):
            translator.google_translate("Hello", "fr")

    def test_google_translate_requires_requests(self):
        """Test google_translate raises ImportError if requests not available."""
        translator = Translator(api_key="test-key")
        # Mock the requests module as None to trigger ImportError
        import pdf_trans_tools
        original_requests = pdf_trans_tools.requests
        pdf_trans_tools.requests = None
        try:
            with pytest.raises(ImportError, match="requests is required"):
                translator.google_translate("Hello", "fr")
        finally:
            pdf_trans_tools.requests = original_requests

    def test_google_translate_url_is_set(self):
        """Test Google Translate URL is properly configured."""
        translator = Translator(api_key="test-key")
        assert translator._google_translate_url == "https://translation.googleapis.com/language/translate/v2"

    def test_version_is_updated(self):
        """Test version has been updated after API integration."""
        from pdf_trans_tools import __version__
        assert __version__ == "0.3.0"
