"""
pdf_trans_tools - PDF Translation Tools
"""

__version__ = "0.4.0"

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

logger = logging.getLogger(__name__)

try:
    import requests
except ImportError:
    requests = None

try:
    from PyPDF2 import PdfReader, PdfWriter
except ImportError:
    PdfReader = None
    PdfWriter = None

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
except ImportError:
    canvas = None

# Valid language codes for Google Translate
VALID_LANGUAGE_CODES = {
    "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh", "ar",
    "hi", "bn", "pa", "ta", "te", "ml", "th", "vi", "id", "ms", "tl",
}


class Translator:
    """Translate PDF documents between languages."""

    def __init__(self, api_key: Optional[str] = None, target_lang: str = "en"):
        self.api_key = api_key
        self.target_lang = target_lang
        self._google_translate_url = "https://translation.googleapis.com/language/translate/v2"

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
        if self.api_key:
            translated_text = self.google_translate(text, lang)
        else:
            translated_text = self._mock_translate(text, lang)

        # Generate output PDF
        self.generate_translated_pdf(translated_text, output_path, title=f"Translated to {lang}")
        return True

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
            ValueError: If API key is not set or translation fails
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

    def extract_text(self, pdf_path: str, password: Optional[str] = None) -> str:
        """
        Extract text from a PDF file with page-by-page support.

        Args:
            pdf_path: Path to PDF file
            password: Optional password for encrypted PDFs

        Returns:
            str: Extracted text content with page separators

        Raises:
            ImportError: If PyPDF2 is not installed
            FileNotFoundError: If the PDF file does not exist
            ValueError: If the PDF is encrypted and no password is provided
        """
        if PdfReader is None:
            raise ImportError("PyPDF2 is required for PDF text extraction. Install with: pip install PyPDF2")

        try:
            reader = PdfReader(pdf_path)
        except FileNotFoundError:
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        if reader.is_encrypted:
            if password is None:
                raise ValueError(f"PDF is encrypted. Provide password parameter.")
            try:
                reader.decrypt(password)
            except Exception:
                raise ValueError(f"Failed to decrypt PDF with provided password.")

        text_parts = []
        for page_num, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(f"--- Page {page_num} ---\n{page_text}")

        return "\n\n".join(text_parts)

    def extract_text_by_page(self, pdf_path: str, password: Optional[str] = None) -> list[tuple[int, str]]:
        """
        Extract text from PDF page by page.

        Args:
            pdf_path: Path to PDF file
            password: Optional password for encrypted PDFs

        Returns:
            list of tuples: [(page_num, text), ...]

        Raises:
            ImportError: If PyPDF2 is not installed
            FileNotFoundError: If the PDF file does not exist
        """
        if PdfReader is None:
            raise ImportError("PyPDF2 is required for PDF text extraction. Install with: pip install PyPDF2")

        try:
            reader = PdfReader(pdf_path)
        except FileNotFoundError:
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        if reader.is_encrypted:
            if password is None:
                raise ValueError(f"PDF is encrypted. Provide password parameter.")
            try:
                reader.decrypt(password)
            except Exception:
                raise ValueError(f"Failed to decrypt PDF with provided password.")

        results = []
        for page_num, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            results.append((page_num, page_text))

        return results

    def get_pdf_info(self, pdf_path: str) -> dict:
        """
        Get basic information about a PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            dict: PDF metadata including page count, encryption status, etc.
        """
        if PdfReader is None:
            raise ImportError("PyPDF2 is required for PDF operations. Install with: pip install PyPDF2")

        try:
            reader = PdfReader(pdf_path)
        except FileNotFoundError:
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        return {
            "page_count": len(reader.pages),
            "is_encrypted": reader.is_encrypted,
            "metadata": reader.metadata if hasattr(reader, 'metadata') else {},
        }

    def generate_translated_pdf(self, text_content: str, output_path: str, title: str = "Translated Document") -> bool:
        """
        Generate a PDF from translated text content.

        Args:
            text_content: The translated text to write to PDF
            output_path: Path where the output PDF should be saved
            title: Title for the document

        Returns:
            bool: True if PDF generation succeeded

        Raises:
            ImportError: If reportlab is not installed
        """
        if canvas is None:
            raise ImportError("reportlab is required for PDF generation. Install with: pip install reportlab")

        c = canvas.Canvas(output_path, pagesize=letter)
        width, height = letter

        # Write title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, title)

        # Write content
        c.setFont("Helvetica", 10)
        y_position = height - 80

        lines = text_content.split('\n')
        for line in lines:
            # Wrap long lines
            if len(line) > 80:
                words = line.split()
                current_line = ""
                for word in words:
                    if len(current_line) + len(word) + 1 <= 80:
                        current_line += (" " + word if current_line else word)
                    else:
                        c.drawString(50, y_position, current_line)
                        y_position -= 12
                        current_line = word
                        if y_position < 50:
                            c.showPage()
                            c.setFont("Helvetica", 10)
                            y_position = height - 50
                if current_line:
                    c.drawString(50, y_position, current_line)
                    y_position -= 12
            else:
                c.drawString(50, y_position, line)
                y_position -= 12

            if y_position < 50:
                c.showPage()
                c.setFont("Helvetica", 10)
                y_position = height - 50

        c.save()
        return True

    def translate_and_generate_pdf(self, input_path: str, output_path: str, target_lang: str = None) -> bool:
        """
        Extract text from PDF, translate it, and generate a new PDF with translated content.

        Args:
            input_path: Path to input PDF file
            output_path: Path to output PDF file
            target_lang: Target language code

        Returns:
            bool: True if the process succeeded

        Raises:
            ValueError: If translation fails or input file cannot be read
        """
        lang = target_lang or self.target_lang

        # Extract text from input PDF
        text = self.extract_text(input_path)
        if not text:
            raise ValueError(f"No text could be extracted from {input_path}")

        # Translate the text (placeholder - uses mock translation)
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
        # This is a placeholder - real implementation would call translation API
        return f"[Translated to {target_lang}]: {text}"
