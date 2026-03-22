"""
pdf_trans_tools validator - Translation consistency validation
"""
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    original_count: int
    translated_count: int
    differences: list[str]
    message: str


class TranslationValidator:
    """Validates that translated content matches original structure."""

    def __init__(self, tolerance: float = 0.1):
        """
        Initialize validator.

        Args:
            tolerance: Allowed difference ratio (0.1 = 10% difference is acceptable)
        """
        self.tolerance = tolerance

    def validate_structure(self, original_text: str, translated_text: str) -> ValidationResult:
        """
        Validate that translated text maintains original structure.

        Args:
            original_text: Original text content
            translated_text: Translated text content

        Returns:
            ValidationResult with details
        """
        differences = []

        # Count pages/sections in original
        original_pages = original_text.count("--- Page")
        translated_pages = translated_text.count("--- Page")

        if original_pages != translated_pages:
            diff_ratio = abs(original_pages - translated_pages) / max(original_pages, 1)
            if diff_ratio > self.tolerance:
                differences.append(
                    f"Page count mismatch: original={original_pages}, translated={translated_pages}"
                )

        # Count paragraphs (separated by double newlines)
        original_paras = len([p for p in original_text.split("\n\n") if p.strip()])
        translated_paras = len([p for p in translated_text.split("\n\n") if p.strip()])

        if original_paras != translated_paras:
            diff_ratio = abs(original_paras - translated_paras) / max(original_paras, 1)
            if diff_ratio > self.tolerance:
                differences.append(
                    f"Paragraph count mismatch: original={original_paras}, translated={translated_paras}"
                )

        # Count lines
        original_lines = len(original_text.split("\n"))
        translated_lines = len(translated_text.split("\n"))

        if original_lines != translated_lines:
            diff_ratio = abs(original_lines - translated_lines) / max(original_lines, 1)
            if diff_ratio > self.tolerance:
                differences.append(
                    f"Line count mismatch: original={original_lines}, translated={translated_lines}"
                )

        # Check if translation is too short or empty
        if not translated_text.strip():
            differences.append("Translated text is empty")
        elif len(translated_text) < len(original_text) * 0.3:
            differences.append(
                f"Translated text is suspiciously short: {len(translated_text)} vs {len(original_text)} chars"
            )

        is_valid = len(differences) == 0

        return ValidationResult(
            is_valid=is_valid,
            original_count=original_pages or 1,
            translated_count=translated_pages or 1,
            differences=differences,
            message="Validation passed" if is_valid else f"Validation failed: {', '.join(differences)}"
        )

    def validate_and_fix(self, original_text: str, translated_text: str) -> tuple[bool, str]:
        """
        Validate translation and attempt to fix common issues.

        Args:
            original_text: Original text
            translated_text: Translated text

        Returns:
            tuple of (is_valid, fixed_text)
        """
        result = self.validate_structure(original_text, translated_text)

        if result.is_valid:
            return True, translated_text

        # Attempt to fix structure issues
        fixed_text = translated_text

        # If page markers are missing but content exists, try to restore
        original_pages = original_text.count("--- Page")
        if original_pages > 0 and "--- Page" not in translated_text:
            # Content was translated but page markers lost - try to restore
            pages_content = original_text.split("--- Page")
            if len(pages_content) > 1:
                logger.warning("Page markers lost in translation, attempting to restore structure")
                fixed_parts = []
                for i, part in enumerate(pages_content[1:], start=1):
                    original_page_lines = part.split("\n")[2:]  # Skip page number
                    original_page_text = "\n".join(original_page_lines).strip()
                    if original_page_text in translated_text:
                        fixed_parts.append(f"--- Page {i} ---\n{translated_text}")
                    else:
                        fixed_parts.append(f"--- Page {i} ---\n{translated_text}")
                if fixed_parts:
                    fixed_text = "\n\n".join(fixed_parts)

        return len(result.differences) == 0, fixed_text


def validate_translation(original_pdf: str, translated_pdf: str, original_text: str, translated_text: str) -> ValidationResult:
    """
    Validate a translation against the original PDF.

    Args:
        original_pdf: Path to original PDF
        translated_pdf: Path to translated PDF
        original_text: Extracted text from original PDF
        translated_text: Extracted text from translated PDF

    Returns:
        ValidationResult with validation details
    """
    validator = TranslationValidator()

    # First validate structure
    result = validator.validate_structure(original_text, translated_text)

    # If validation fails, try to fix
    if not result.is_valid:
        logger.warning(f"Translation validation issues: {result.differences}")
        is_valid, fixed_text = validator.validate_and_fix(original_text, translated_text)
        if is_valid:
            result.is_valid = True
            result.message = "Validation passed after fixes"
        else:
            result.differences.append("Automatic fix could not resolve all issues")

    return result
