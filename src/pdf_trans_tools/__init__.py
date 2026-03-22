"""
pdf_trans_tools - PDF Translation Tools
Main package entry point.
Orchestrates PDF operations, translation, and validation.
"""

__version__ = "1.0.0"

import logging
import re
import time
from typing import Optional

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
from pdf_trans_tools.backends import TranslationBackend, GoogleTranslateBackend, MockBackend, BackendManager
from pdf_trans_tools.cache import TranslationCache, get_cache
from pdf_trans_tools.config import Config, load_config
from pdf_trans_tools.validator import TranslationValidator, validate_translation, ValidationResult
from pdf_trans_tools.pdf_reader import PdfReaderHelper
from pdf_trans_tools.pdf_writer import PdfWriterHelper
from pdf_trans_tools.batch import BatchProcessor, BatchResult
from pdf_trans_tools.retry import with_retry, RetryExhaustedError, RetryStats, get_retry_stats

logger = logging.getLogger(__name__)

try:
    import requests
except ImportError:
    requests = None

# Valid language codes for Google Translate
VALID_LANGUAGE_CODES = {
    "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh", "ar",
    "hi", "bn", "pa", "ta", "te", "ml", "th", "vi", "id", "ms", "tl",
}


class Translator:
    """Translate PDF documents between languages.

    This is the main orchestrator class that coordinates:
    - PDF reading (via PdfReaderHelper)
    - PDF writing (via PdfWriterHelper)
    - Translation (via backends)
    - Caching
    - Validation
    """

    def __init__(self, api_key: Optional[str] = None, target_lang: str = "en", backend: Optional[TranslationBackend] = None, use_cache: bool = True):
        """
        Initialize Translator.

        Args:
            api_key: Google Translate API key
            target_lang: Default target language code
            backend: Optional custom translation backend
            use_cache: Whether to use translation caching
        """
        self.api_key = api_key
        self.target_lang = target_lang
        self._google_translate_url = "https://translation.googleapis.com/language/translate/v2"
        self._use_cache = use_cache
        self._cache = get_cache() if use_cache else None

        # PDF helpers
        self._pdf_reader = PdfReaderHelper()
        self._pdf_writer = PdfWriterHelper()

        # Backend manager
        self._backend_manager = BackendManager()
        if backend:
            self._backend_manager.register("default", backend)
        elif api_key:
            self._backend_manager.register("google", GoogleTranslateBackend(api_key))
        else:
            self._backend_manager.register("mock", MockBackend())

    def translate(self, text: str, target_lang: str = None, source_lang: str = "") -> str:
        """
        Translate text using the registered backend.

        Args:
            text: Text to translate
            target_lang: Target language code
            source_lang: Source language code (auto-detect if empty)

        Returns:
            str: Translated text
        """
        lang = target_lang or self.target_lang

        # Check cache first
        if self._cache:
            cached = self._cache.get(text, lang, source_lang)
            if cached:
                logger.debug(f"Cache hit for translation ({len(text)} chars)")
                return cached

        backend = self._backend_manager.get("default") or self._backend_manager.get("google")
        if backend:
            result = backend.translate(text, lang, source_lang)
        else:
            result = self._mock_translate(text, lang)

        # Store in cache
        if self._cache and result:
            self._cache.put(text, lang, result, source_lang)
            logger.debug(f"Cached translation ({len(text)} chars)")

        return result

    def cache_stats(self) -> dict:
        """Get cache statistics."""
        if self._cache:
            return self._cache.stats()
        return {}

    def extract_text(self, pdf_path: str, password: Optional[str] = None) -> str:
        """
        Extract text from a PDF file with page-by-page support.

        Args:
            pdf_path: Path to PDF file
            password: Optional password for encrypted PDFs

        Returns:
            str: Extracted text content with page separators
        """
        return self._pdf_reader.extract_text(pdf_path, password)

    def extract_text_by_page(self, pdf_path: str, password: Optional[str] = None) -> list[tuple[int, str]]:
        """
        Extract text from PDF page by page.

        Args:
            pdf_path: Path to PDF file
            password: Optional password for encrypted PDFs

        Returns:
            list of tuples: [(page_num, text), ...]
        """
        return self._pdf_reader.extract_text_by_page(pdf_path, password)

    def get_pdf_info(self, pdf_path: str) -> dict:
        """
        Get basic information about a PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            dict: PDF metadata including page count, encryption status, etc.
        """
        return self._pdf_reader.get_info(pdf_path)

    def generate_translated_pdf(self, text_content: str, output_path: str, title: str = "Translated Document") -> bool:
        """
        Generate a PDF from translated text content.

        Args:
            text_content: The translated text to write to PDF
            output_path: Path where the output PDF should be saved
            title: Title for the document

        Returns:
            bool: True if PDF generation succeeded
        """
        return self._pdf_writer.generate_pdf(text_content, output_path, title)

    def translate_pdf(self, input_path: str, output_path: str, target_lang: Optional[str] = None) -> bool:
        """
        Translate a PDF file to the target language.

        Args:
            input_path: Path to input PDF file
            output_path: Path to output PDF file
            target_lang: Target language code (e.g., 'en', 'zh', 'es')

        Returns:
            bool: True if translation succeeded
        """
        lang = target_lang or self.target_lang

        # Extract text from PDF
        text = self.extract_text(input_path)
        if not text:
            return False

        # Translate the text
        translated_text = self.translate(text, lang)

        # Generate output PDF
        self.generate_translated_pdf(translated_text, output_path, title=f"Translated to {lang}")
        return True

    def translate_pdf_with_validation(self, input_path: str, output_path: str, target_lang: Optional[str] = None) -> tuple[bool, ValidationResult]:
        """
        Translate a PDF file with consistency validation.

        Validates that the translated PDF maintains the same structure as the original.
        If inconsistencies are found, automatic fixes are attempted.

        Args:
            input_path: Path to input PDF file
            output_path: Path to output PDF file
            target_lang: Target language code (e.g., 'en', 'zh', 'es')

        Returns:
            tuple of (success: bool, validation_result: ValidationResult)
        """
        lang = target_lang or self.target_lang
        validator = TranslationValidator()

        # Extract text from PDF
        original_text = self.extract_text(input_path)
        if not original_text:
            return False, ValidationResult(
                is_valid=False,
                original_count=0,
                translated_count=0,
                differences=["Could not extract text from original PDF"],
                message="Extraction failed"
            )

        # Translate the text
        translated_text = self.translate(original_text, lang)

        # Validate structure
        validation_result = validator.validate_structure(original_text, translated_text)

        # If validation fails, try to fix
        if not validation_result.is_valid:
            logger.warning(f"Translation validation issues found: {validation_result.differences}")
            is_fixed, fixed_text = validator.validate_and_fix(original_text, translated_text)
            if is_fixed:
                translated_text = fixed_text
                validation_result.is_valid = True
                validation_result.message = "Validation passed after automatic fix"
                logger.info("Automatic fix applied successfully")
            else:
                validation_result.differences.append("Automatic fix could not resolve all issues")

        # Generate output PDF
        self.generate_translated_pdf(translated_text, output_path, title=f"Translated to {lang}")
        return True, validation_result

    def google_translate(self, text: str, target_lang: str, source_lang: str = "") -> str:
        """
        Translate text using Google Cloud Translation API.

        Args:
            text: Text to translate
            target_lang: Target language code (e.g., 'en', 'zh', 'es')
            source_lang: Source language code (auto-detect if empty)

        Returns:
            str: Translated text

        Raises:
            ImportError: If requests library is not installed
            TranslationAPIError: If API key is not set or translation fails
        """
        if requests is None:
            raise ImportError("requests is required for Google Translate. Install with: pip install requests")

        if not self.api_key:
            raise TranslationAPIError("API key is required for Google Translate. Set api_key in Translator constructor.")

        # Validate language code
        if target_lang not in VALID_LANGUAGE_CODES:
            raise InvalidLanguageError(f"Invalid language code: {target_lang}. Valid codes: {', '.join(sorted(VALID_LANGUAGE_CODES))}")

        # Google Translate API has a limit of 128KB per request
        # Split text into chunks if necessary
        max_chars = 5000  # Safe limit for API
        if len(text) > max_chars:
            return self._translate_large_text(text, target_lang, source_lang)

        params = {
            "key": self.api_key,
            "q": text,
            "target": target_lang,
            "format": "text"
        }
        if source_lang:
            params["source"] = source_lang

        try:
            logger.debug(f"Calling Google Translate API for {len(text)} characters")
            response = requests.post(self._google_translate_url, params=params, timeout=30)
            response.raise_for_status()
            result = response.json()

            if "data" in result and "translations" in result["data"]:
                translated = result["data"]["translations"][0]["translatedText"]
                logger.debug(f"Translation successful, {len(translated)} characters")
                return translated
            else:
                raise TranslationAPIError(f"Unexpected API response: {result}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise TranslationRateLimitError(f"API rate limit exceeded: {e}")
            raise TranslationAPIError(f"Google Translate API HTTP error: {e}")
        except requests.exceptions.RequestException as e:
            raise TranslationAPIError(f"Google Translate API error: {e}")

    def _translate_large_text(self, text: str, target_lang: str, source_lang: str = "") -> str:
        """
        Translate large text by splitting into chunks and translating each.

        Args:
            text: Text to translate
            target_lang: Target language code
            source_lang: Source language code

        Returns:
            str: Translated text
        """
        # Split by sentences or paragraphs for better context
        chunks = []
        current_chunk = []
        current_length = 0
        max_chars = 4000  # Leave room for API overhead

        # Simple split by sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)

        for sentence in sentences:
            if current_length + len(sentence) > max_chars and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_length = 0
            current_chunk.append(sentence)
            current_length += len(sentence)

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        # Translate each chunk with rate limiting
        translated_chunks = []
        for i, chunk in enumerate(chunks):
            translated = self.google_translate(chunk, target_lang, source_lang)
            translated_chunks.append(translated)
            # Rate limiting to avoid API quotas
            if i < len(chunks) - 1:
                time.sleep(0.1)

        return " ".join(translated_chunks)

    def translate_and_generate_pdf(self, input_path: str, output_path: str, target_lang: str = None) -> bool:
        """
        Extract text from PDF, translate it, and generate a new PDF with translated content.

        Args:
            input_path: Path to input PDF file
            output_path: Path to output PDF file
            target_lang: Target language code

        Returns:
            bool: True if the process succeeded
        """
        lang = target_lang or self.target_lang

        # Extract text from input PDF
        text = self.extract_text(input_path)
        if not text:
            raise PDFReadError(f"No text could be extracted from {input_path}")

        # Translate the text
        translated_text = self._mock_translate(text, lang)

        # Generate output PDF
        self.generate_translated_pdf(translated_text, output_path, title=f"Translated to {lang}")
        return True

    def _mock_translate(self, text: str, target_lang: str) -> str:
        """
        Mock translation for testing purposes.
        In production, this would call an actual translation API.

        Args:
            text: Text to translate
            target_lang: Target language code

        Returns:
            str: Translated text (mock implementation)
        """
        return f"[Translated to {target_lang}]: {text}"
