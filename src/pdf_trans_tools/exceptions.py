"""
pdf_trans_tools exceptions - Custom exception hierarchy for PDF translation
"""


class PDFTranslateError(Exception):
    """Base exception for pdf_trans_tools errors."""
    pass


class PDFReadError(PDFTranslateError):
    """Raised when a PDF file cannot be read."""
    pass


class PDFWriteError(PDFTranslateError):
    """Raised when a PDF cannot be written."""
    pass


class PDFEncryptedError(PDFTranslateError):
    """Raised when a PDF is encrypted and requires a password."""
    pass


class TranslationError(PDFTranslateError):
    """Raised when translation fails."""
    pass


class TranslationAPIError(TranslationError):
    """Raised when the translation API returns an error."""
    pass


class TranslationRateLimitError(TranslationError):
    """Raised when API rate limit is exceeded."""
    pass


class InvalidLanguageError(PDFTranslateError):
    """Raised when an invalid language code is provided."""
    pass
