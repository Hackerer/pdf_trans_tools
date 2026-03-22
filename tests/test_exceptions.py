"""Tests for exception classes"""
import pytest
from pdf_trans_tools import Translator
from pdf_trans_tools.exceptions import (
    PDFTranslateError,
    PDFReadError,
    PDFWriteError,
    PDFEncryptedError,
    TranslationError,
    TranslationAPIError,
    TranslationRateLimitError,
    InvalidLanguageError,
)


class TestExceptions:
    """Test cases for exception classes."""

    def test_pdf_translate_error_exists(self):
        """Test PDFTranslateError exists."""
        assert PDFTranslateError is not None

    def test_pdf_read_error_exists(self):
        """Test PDFReadError exists."""
        assert PDFReadError is not None

    def test_pdf_write_error_exists(self):
        """Test PDFWriteError exists."""
        assert PDFWriteError is not None

    def test_pdf_encrypted_error_exists(self):
        """Test PDFEncryptedError exists."""
        assert PDFEncryptedError is not None

    def test_translation_error_exists(self):
        """Test TranslationError exists."""
        assert TranslationError is not None

    def test_translation_api_error_exists(self):
        """Test TranslationAPIError exists."""
        assert TranslationAPIError is not None

    def test_translation_rate_limit_error_exists(self):
        """Test TranslationRateLimitError exists."""
        assert TranslationRateLimitError is not None

    def test_invalid_language_error_exists(self):
        """Test InvalidLanguageError exists."""
        assert InvalidLanguageError is not None

    def test_exception_hierarchy(self):
        """Test exception hierarchy."""
        assert issubclass(PDFReadError, PDFTranslateError)
        assert issubclass(PDFWriteError, PDFTranslateError)
        assert issubclass(PDFEncryptedError, PDFTranslateError)
        assert issubclass(TranslationError, PDFTranslateError)
        assert issubclass(TranslationAPIError, TranslationError)
        assert issubclass(TranslationRateLimitError, TranslationError)
        assert issubclass(InvalidLanguageError, PDFTranslateError)

    def test_can_raise_translation_api_error(self):
        """Test TranslationAPIError can be raised."""
        translator = Translator()
        with pytest.raises(TranslationAPIError):
            translator.google_translate("test", "invalid_lang")

    def test_invalid_language_error_message(self):
        """Test InvalidLanguageError has proper message."""
        with pytest.raises(InvalidLanguageError, match="Invalid language code"):
            raise InvalidLanguageError("Invalid language code: xyz")
