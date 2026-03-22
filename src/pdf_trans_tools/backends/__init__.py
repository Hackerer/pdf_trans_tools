"""
pdf_trans_tools backends - Translation backend abstraction
"""
from abc import ABC, abstractmethod
from typing import Optional


class TranslationBackend(ABC):
    """Abstract base class for translation backends."""

    @abstractmethod
    def translate(self, text: str, target_lang: str, source_lang: str = "") -> str:
        """
        Translate text to target language.

        Args:
            text: Text to translate
            target_lang: Target language code
            source_lang: Source language code (auto-detect if empty)

        Returns:
            str: Translated text
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this backend is available (has required credentials/API).

        Returns:
            bool: True if backend can be used
        """
        pass


class GoogleTranslateBackend(TranslationBackend):
    """Google Cloud Translation API backend."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._url = "https://translation.googleapis.com/language/translate/v2"

    def translate(self, text: str, target_lang: str, source_lang: str = "") -> str:
        import requests

        params = {
            "key": self.api_key,
            "q": text,
            "target": target_lang,
            "format": "text"
        }
        if source_lang:
            params["source"] = source_lang

        response = requests.post(self._url, params=params, timeout=30)
        response.raise_for_status()
        result = response.json()

        if "data" in result and "translations" in result["data"]:
            return result["data"]["translations"][0]["translatedText"]
        raise ValueError(f"Unexpected API response: {result}")

    def is_available(self) -> bool:
        return bool(self.api_key)


class MockBackend(TranslationBackend):
    """Mock backend for testing."""

    def __init__(self):
        pass

    def translate(self, text: str, target_lang: str, source_lang: str = "") -> str:
        return f"[Translated to {target_lang}]: {text}"

    def is_available(self) -> bool:
        return True


class BackendManager:
    """Manages multiple translation backends."""

    def __init__(self):
        self._backends = {}

    def register(self, name: str, backend: TranslationBackend) -> None:
        """Register a translation backend."""
        self._backends[name] = backend

    def get(self, name: str) -> Optional[TranslationBackend]:
        """Get a backend by name."""
        return self._backends.get(name)

    def list_backends(self) -> list[str]:
        """List all registered backend names."""
        return list(self._backends.keys())

    def get_available(self) -> list[str]:
        """List all backends that are currently available."""
        return [name for name, backend in self._backends.items() if backend.is_available()]
