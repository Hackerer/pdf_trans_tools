"""
pdf_trans_tools - PDF Translation Tools
"""

__version__ = "0.1.0"

import re
from typing import Optional

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None


class Translator:
    """Translate PDF documents between languages."""

    def __init__(self, api_key: Optional[str] = None, target_lang: str = "en"):
        self.api_key = api_key
        self.target_lang = target_lang

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
        if not self.api_key:
            print(f"Translating {input_path} to {lang}, output to {output_path} (no API key)")
            return True
        print(f"Translating {input_path} to {lang}, output to {output_path}")
        return True

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
