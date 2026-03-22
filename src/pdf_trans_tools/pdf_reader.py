"""
pdf_trans_tools pdf_reader - PDF text extraction module
"""
import logging
from typing import Optional

from pdf_trans_tools.exceptions import PDFReadError, PDFEncryptedError

logger = logging.getLogger(__name__)

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None


class PdfReaderHelper:
    """Handles PDF text extraction operations."""

    def __init__(self):
        if PdfReader is None:
            raise ImportError("PyPDF2 is required for PDF operations. Install with: pip install PyPDF2")

    def extract_text(self, pdf_path: str, password: Optional[str] = None) -> str:
        """
        Extract text from a PDF file with page-by-page support.

        Args:
            pdf_path: Path to PDF file
            password: Optional password for encrypted PDFs

        Returns:
            str: Extracted text content with page separators

        Raises:
            PDFReadError: If PDF cannot be read
            PDFEncryptedError: If PDF is encrypted
        """
        try:
            reader = PdfReader(pdf_path)
        except FileNotFoundError:
            raise PDFReadError(f"PDF file not found: {pdf_path}")
        except Exception as e:
            raise PDFReadError(f"Failed to read PDF: {e}")

        if reader.is_encrypted:
            if password is None:
                raise PDFEncryptedError(f"PDF is encrypted. Provide password parameter.")
            try:
                reader.decrypt(password)
            except Exception:
                raise PDFEncryptedError(f"Failed to decrypt PDF with provided password.")

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
            PDFReadError: If PDF cannot be read
        """
        try:
            reader = PdfReader(pdf_path)
        except FileNotFoundError:
            raise PDFReadError(f"PDF file not found: {pdf_path}")
        except Exception as e:
            raise PDFReadError(f"Failed to read PDF: {e}")

        if reader.is_encrypted:
            if password is None:
                raise PDFEncryptedError(f"PDF is encrypted. Provide password parameter.")
            try:
                reader.decrypt(password)
            except Exception:
                raise PDFEncryptedError(f"Failed to decrypt PDF with provided password.")

        results = []
        for page_num, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            results.append((page_num, page_text))

        return results

    def get_info(self, pdf_path: str) -> dict:
        """
        Get basic information about a PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            dict: PDF metadata including page count, encryption status, etc.
        """
        try:
            reader = PdfReader(pdf_path)
        except FileNotFoundError:
            raise PDFReadError(f"PDF file not found: {pdf_path}")
        except Exception as e:
            raise PDFReadError(f"Failed to read PDF: {e}")

        return {
            "page_count": len(reader.pages),
            "is_encrypted": reader.is_encrypted,
            "metadata": reader.metadata if hasattr(reader, 'metadata') else {},
        }
