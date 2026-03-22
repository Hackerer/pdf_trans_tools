"""Tests for backend modules"""
import pytest
from pdf_trans_tools.backends import (
    TranslationBackend,
    GoogleTranslateBackend,
    MockBackend,
    BackendManager,
)


class TestBackends:
    """Test cases for translation backends."""

    def test_translation_backend_is_abstract(self):
        """Test TranslationBackend cannot be instantiated directly."""
        with pytest.raises(TypeError):
            TranslationBackend()

    def test_mock_backend_translate(self):
        """Test MockBackend translate method."""
        backend = MockBackend()
        result = backend.translate("Hello", "fr")
        assert "fr" in result
        assert "Hello" in result

    def test_mock_backend_is_available(self):
        """Test MockBackend is always available."""
        backend = MockBackend()
        assert backend.is_available() is True

    def test_google_backend_init(self):
        """Test GoogleTranslateBackend initialization."""
        backend = GoogleTranslateBackend("test-key")
        assert backend.api_key == "test-key"

    def test_google_backend_is_available_with_key(self):
        """Test GoogleTranslateBackend availability with key."""
        backend = GoogleTranslateBackend("test-key")
        assert backend.is_available() is True

    def test_google_backend_is_not_available_without_key(self):
        """Test GoogleTranslateBackend not available without key."""
        backend = GoogleTranslateBackend("")
        assert backend.is_available() is False

    def test_backend_manager_register(self):
        """Test BackendManager registration."""
        manager = BackendManager()
        backend = MockBackend()
        manager.register("mock", backend)
        assert manager.get("mock") is backend

    def test_backend_manager_list_backends(self):
        """Test BackendManager list_backends."""
        manager = BackendManager()
        manager.register("mock", MockBackend())
        manager.register("google", GoogleTranslateBackend("key"))
        assert "mock" in manager.list_backends()
        assert "google" in manager.list_backends()

    def test_backend_manager_get_available(self):
        """Test BackendManager get_available."""
        manager = BackendManager()
        manager.register("mock", MockBackend())  # Always available
        manager.register("google", GoogleTranslateBackend(""))  # Not available
        available = manager.get_available()
        assert "mock" in available
        assert "google" not in available

    def test_backend_manager_get_nonexistent(self):
        """Test BackendManager returns None for nonexistent backend."""
        manager = BackendManager()
        assert manager.get("nonexistent") is None
