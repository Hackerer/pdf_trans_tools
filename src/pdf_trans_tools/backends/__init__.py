"""
pdf_trans_tools backends - Translation backend abstraction
"""
from abc import ABC, abstractmethod
from typing import Optional
import re
import urllib.parse


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


class MyMemoryBackend(TranslationBackend):
    """Free MyMemory Translation API backend - no API key required."""

    def __init__(self):
        self._url = "https://api.mymemory.translated.net/get"
        self._lang_codes = {
            "en": "en", "zh": "zh-CN", "ja": "ja", "ko": "ko",
            "fr": "fr", "de": "de", "es": "es", "it": "it",
            "pt": "pt", "ru": "ru", "ar": "ar", "hi": "hi"
        }

    def _convert_lang(self, code: str) -> str:
        """Convert language code to MyMemory format."""
        return self._lang_codes.get(code, code)

    def translate(self, text: str, target_lang: str, source_lang: str = "") -> str:
        """Translate using MyMemory API (free, no API key needed)."""
        import requests

        # MyMemory has a 500 char limit per request, so we split by sentences
        lang_pair = f"{self._convert_lang(source_lang)}|{self._convert_lang(target_lang)}" if source_lang else f"en|{self._convert_lang(target_lang)}"

        # Split text into chunks (max 500 chars each)
        chunks = self._split_text(text)

        translated_parts = []
        for chunk in chunks:
            params = {
                "q": chunk,
                "langpair": lang_pair
            }

            try:
                response = requests.get(self._url, params=params, timeout=30)
                response.raise_for_status()
                result = response.json()

                if result.get("responseStatus") == 200:
                    translated_parts.append(result["responseData"]["translatedText"])
                else:
                    # Fallback: return original if API fails
                    translated_parts.append(chunk)
            except Exception:
                # Fallback: return original
                translated_parts.append(chunk)

        return " ".join(translated_parts)

    def _split_text(self, text: str, max_len: int = 450) -> list[str]:
        """Split text into chunks that respect sentence boundaries."""
        if len(text) <= max_len:
            return [text]

        # Split by sentence-ending punctuation
        sentences = re.split(r'(?<=[.!?。！？])\s+', text)

        chunks = []
        current_chunk = []

        for sentence in sentences:
            if sum(len(s) for s in current_chunk) + len(sentence) <= max_len:
                current_chunk.append(sentence)
            else:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def is_available(self) -> bool:
        return True  # Free API, always available


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
