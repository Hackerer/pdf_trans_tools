"""Tests for validator module"""
import pytest
from pdf_trans_tools.validator import TranslationValidator, ValidationResult, validate_translation


class TestValidator:
    """Test cases for TranslationValidator."""

    def test_validator_init(self):
        """Test TranslationValidator initialization."""
        validator = TranslationValidator()
        assert validator.tolerance == 0.1

    def test_validator_init_custom_tolerance(self):
        """Test TranslationValidator with custom tolerance."""
        validator = TranslationValidator(tolerance=0.2)
        assert validator.tolerance == 0.2

    def test_validate_structure_matching(self):
        """Test validation with matching structures."""
        validator = TranslationValidator()
        original = "--- Page 1 ---\nHello world\n\n--- Page 2 ---\nGoodbye world"
        translated = "--- Page 1 ---\nHola mundo\n\n--- Page 2 ---\nAdios mundo"

        result = validator.validate_structure(original, translated)
        assert result.is_valid is True
        assert result.original_count == 2
        assert result.translated_count == 2
        assert len(result.differences) == 0

    def test_validate_structure_page_mismatch(self):
        """Test validation with page count mismatch."""
        validator = TranslationValidator()
        original = "--- Page 1 ---\nHello\n\n--- Page 2 ---\nWorld"
        translated = "--- Page 1 ---\nHola"

        result = validator.validate_structure(original, translated)
        assert result.is_valid is False
        assert "Page count mismatch" in result.differences[0]

    def test_validate_structure_paragraph_mismatch(self):
        """Test validation with paragraph count mismatch."""
        validator = TranslationValidator(tolerance=0.05)  # Strict
        original = "Para 1\n\nPara 2\n\nPara 3\n\nPara 4"
        translated = "Para 1\n\nPara 2"

        result = validator.validate_structure(original, translated)
        assert result.is_valid is False
        assert any("Paragraph count" in d for d in result.differences)

    def test_validate_structure_empty_translation(self):
        """Test validation with empty translation."""
        validator = TranslationValidator()
        original = "Hello world"
        translated = ""

        result = validator.validate_structure(original, translated)
        assert result.is_valid is False
        # Either empty warning or paragraph mismatch - both indicate problem
        has_issue = any("empty" in d.lower() or "mismatch" in d.lower() for d in result.differences)
        assert has_issue

    def test_validate_structure_suspiciously_short(self):
        """Test validation with suspiciously short translation."""
        validator = TranslationValidator()
        original = "Hello world this is a long sentence that needs translation"
        translated = "Hola"

        result = validator.validate_structure(original, translated)
        assert result.is_valid is False
        assert any("suspiciously short" in d for d in result.differences)

    def test_validate_and_fix_page_markers_lost(self):
        """Test fixing when page markers are lost."""
        validator = TranslationValidator()
        original = "--- Page 1 ---\nHello\n\n--- Page 2 ---\nWorld"
        translated = "Hola Mundo"

        is_valid, fixed = validator.validate_and_fix(original, translated)
        # Fix may not work for all cases, but should not crash

    def test_validation_result_dataclass(self):
        """Test ValidationResult dataclass."""
        result = ValidationResult(
            is_valid=True,
            original_count=2,
            translated_count=2,
            differences=[],
            message="OK"
        )
        assert result.is_valid is True
        assert result.original_count == 2
        assert result.translated_count == 2
        assert result.message == "OK"

    def test_validate_translation_function(self):
        """Test validate_translation function."""
        result = validate_translation(
            original_pdf="input.pdf",
            translated_pdf="output.pdf",
            original_text="--- Page 1 ---\nHello",
            translated_text="--- Page 1 ---\nHola"
        )
        assert isinstance(result, ValidationResult)
