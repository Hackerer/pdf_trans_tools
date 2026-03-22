"""
pdf_trans_tools cache - Translation result caching
"""
import hashlib
import time
from collections import OrderedDict
from typing import Optional


class TranslationCache:
    """LRU cache for translation results."""

    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """
        Initialize translation cache.

        Args:
            max_size: Maximum number of entries in cache
            ttl: Time-to-live in seconds for cache entries
        """
        self._cache = OrderedDict()
        self._timestamps = {}
        self._max_size = max_size
        self._ttl = ttl
        self._hits = 0
        self._misses = 0

    def _make_key(self, text: str, target_lang: str, source_lang: str = "") -> str:
        """Create a cache key from translation parameters."""
        content = f"{text}|{target_lang}|{source_lang}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get(self, text: str, target_lang: str, source_lang: str = "") -> Optional[str]:
        """
        Get cached translation.

        Args:
            text: Original text
            target_lang: Target language code
            source_lang: Source language code

        Returns:
            Cached translation or None if not found/expired
        """
        key = self._make_key(text, target_lang, source_lang)

        if key not in self._cache:
            self._misses += 1
            return None

        # Check if expired
        timestamp = self._timestamps.get(key, 0)
        if time.time() - timestamp > self._ttl:
            # Remove expired entry
            del self._cache[key]
            del self._timestamps[key]
            self._misses += 1
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(key)
        self._hits += 1
        return self._cache[key]

    def put(self, text: str, target_lang: str, translated: str, source_lang: str = "") -> None:
        """
        Store translation in cache.

        Args:
            text: Original text
            target_lang: Target language code
            translated: Translated text
            source_lang: Source language code
        """
        key = self._make_key(text, target_lang, source_lang)

        # Remove oldest if at capacity
        if len(self._cache) >= self._max_size and key not in self._cache:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            del self._timestamps[oldest_key]

        self._cache[key] = translated
        self._timestamps[key] = time.time()
        self._cache.move_to_end(key)

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._timestamps.clear()
        self._hits = 0
        self._misses = 0

    def stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            dict with hits, misses, size, hit_rate
        """
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0
        return {
            "hits": self._hits,
            "misses": self._misses,
            "size": len(self._cache),
            "max_size": self._max_size,
            "hit_rate": hit_rate
        }


# Global cache instance
_global_cache = TranslationCache()


def get_cache() -> TranslationCache:
    """Get the global cache instance."""
    return _global_cache
