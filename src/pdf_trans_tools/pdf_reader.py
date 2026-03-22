"""
pdf_trans_tools pdf_reader - PDF text extraction module
"""
import logging
import hashlib
from typing import Optional, Tuple, List
from functools import lru_cache

from pdf_trans_tools.exceptions import PDFReadError, PDFEncryptedError

logger = logging.getLogger(__name__)

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None


class PdfReaderHelper:
    """Handles PDF text extraction operations with caching."""

    def __init__(self, cache_size: int = 100):
        if PdfReader is None:
            raise ImportError("PyPDF2 is required for PDF operations. Install with: pip install PyPDF2")
        self._cache = {}
        self._cache_size = cache_size

    def _get_file_key(self, pdf_path: str) -> str:
        """Generate cache key based on file path and modification time."""
        import os
        try:
            mtime = os.path.getmtime(pdf_path)
            return hashlib.md5(f"{pdf_path}:{mtime}".encode()).hexdigest()
        except:
            return hashlib.md5(pdf_path.encode()).hexdigest()

    def _open_pdf(self, pdf_path: str, password: Optional[str] = None) -> Tuple['PdfReader', dict]:
        """
        Open PDF file and return reader with info.

        Returns:
            Tuple of (reader, info_dict)
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

        info = {
            "page_count": len(reader.pages),
            "is_encrypted": reader.is_encrypted,
            "metadata": reader.metadata if hasattr(reader, 'metadata') else {},
        }

        return reader, info

    def extract_text(self, pdf_path: str, password: Optional[str] = None, max_pages: Optional[int] = None) -> str:
        """
        Extract text from a PDF file with page-by-page support.

        Args:
            pdf_path: Path to PDF file
            password: Optional password for encrypted PDFs
            max_pages: Optional limit on pages to extract (for preview)

        Returns:
            str: Extracted text content with page separators

        Raises:
            PDFReadError: If PDF cannot be read
            PDFEncryptedError: If PDF is encrypted
        """
        cache_key = f"{self._get_file_key(pdf_path)}:{password}:{max_pages}"

        # Check cache
        if cache_key in self._cache:
            logger.debug(f"Cache hit for PDF extraction: {pdf_path}")
            return self._cache[cache_key]

        reader, info = self._open_pdf(pdf_path, password)

        text_parts = []
        pages = reader.pages[:max_pages] if max_pages else reader.pages

        for page_num, page in enumerate(pages, start=1):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(f"--- Page {page_num} ---\n{page_text}")

        result = "\n\n".join(text_parts)

        # Cache result
        if len(self._cache) >= self._cache_size:
            # Remove oldest entry
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        self._cache[cache_key] = result

        return result

    def extract_text_by_page(self, pdf_path: str, password: Optional[str] = None) -> List[Tuple[int, str]]:
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
        reader, _ = self._open_pdf(pdf_path, password)

        results = []
        for page_num, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            results.append((page_num, page_text))

        return results

    def get_info(self, pdf_path: str) -> dict:
        """
        Get basic information about a PDF file.
        """
        _, info = self._open_pdf(pdf_path)
        return info

    def clear_cache(self):
        """Clear the extraction cache."""
        self._cache.clear()
