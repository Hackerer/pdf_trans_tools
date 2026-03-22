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
        # Extended language code mapping for MyMemory API
        self._lang_codes = {
            "en": "en", "zh": "zh-CN", "ja": "ja", "ko": "ko",
            "fr": "fr", "de": "de", "es": "es", "it": "it",
            "pt": "pt-BR", "ru": "ru", "ar": "ar", "hi": "hi",
            "bn": "bn", "pa": "pa", "ta": "ta", "te": "te",
            "ml": "ml", "th": "th", "vi": "vi", "id": "id",
            "ms": "ms", "tl": "tl", "tr": "tr", "nl": "nl",
            "pl": "pl", "sv": "sv", "da": "da", "no": "no",
            "fi": "fi", "el": "el", "he": "he", "cs": "cs",
            "hu": "hu", "ro": "ro", "uk": "uk", "bg": "bg"
        }
        self._max_retries = 2
        self._retry_delay = 0.5  # seconds
        self._session = None

    def _get_session(self):
        """Get or create requests session for connection pooling."""
        import requests
        if self._session is None:
            self._session = requests.Session()
            adapter = requests.adapters.HTTPAdapter(
                pool_connections=10,
                pool_maxsize=10,
                max_retries=0
            )
            self._session.mount('https://', adapter)
        return self._session

    def _convert_lang(self, code: str) -> str:
        """Convert language code to MyMemory format."""
        return self._lang_codes.get(code, code)

    def translate(self, text: str, target_lang: str, source_lang: str = "") -> str:
        """Translate using MyMemory API (free, no API key needed)."""
        import time

        # MyMemory has a 500 char limit per request, so we split by sentences
        lang_pair = f"{self._convert_lang(source_lang)}|{self._convert_lang(target_lang)}" if source_lang else f"en|{self._convert_lang(target_lang)}"

        # Split text into chunks (max 500 chars each)
        chunks = self._split_text(text)

        translated_parts = []
        session = self._get_session()

        for chunk in chunks:
            params = {
                "q": chunk,
                "langpair": lang_pair
            }

            for retry in range(self._max_retries):
                try:
                    response = session.get(self._url, params=params, timeout=15)
                    response.raise_for_status()
                    result = response.json()

                    if result.get("responseStatus") == 200:
                        translated_parts.append(result["responseData"]["translatedText"])
                        break
                    elif result.get("responseStatus") == 429:
                        # Rate limited - wait and retry
                        time.sleep(self._retry_delay * (retry + 1))
                        continue
                    else:
                        # Other error - fallback to original
                        translated_parts.append(chunk)
                        break
                except Exception:
                    if retry < self._max_retries - 1:
                        time.sleep(self._retry_delay * (retry + 1))
                        continue
                    # Fallback: return original
                    translated_parts.append(chunk)

        return " ".join(translated_parts)

    def _split_text(self, text: str, max_len: int = 450) -> list[str]:
        """Split text into chunks that respect sentence and paragraph boundaries."""
        if len(text) <= max_len:
            return [text]

        # First try to split by paragraphs (double newline or double space)
        paragraphs = re.split(r'\n\s*\n|\r\n\s*\r\n', text)

        chunks = []
        current_chunk = []

        for paragraph in paragraphs:
            # If single paragraph is too long, split by sentences
            if len(paragraph) <= max_len:
                if sum(len(s) for s in current_chunk) + len(paragraph) + 1 <= max_len:
                    current_chunk.append(paragraph)
                else:
                    if current_chunk:
                        chunks.append("\n".join(current_chunk))
                    current_chunk = [paragraph]
            else:
                # Split long paragraph by sentences
                sentences = re.split(r'(?<=[.!?。！？])\s+', paragraph)
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
