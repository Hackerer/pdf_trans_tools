"""Tests for cache module"""
import time
import pytest
from pdf_trans_tools.cache import TranslationCache, get_cache


class TestCache:
    """Test cases for TranslationCache."""

    def test_cache_init(self):
        """Test TranslationCache initialization."""
        cache = TranslationCache()
        assert cache._max_size == 1000
        assert cache._ttl == 3600

    def test_cache_init_with_params(self):
        """Test TranslationCache with custom parameters."""
        cache = TranslationCache(max_size=100, ttl=60)
        assert cache._max_size == 100
        assert cache._ttl == 60

    def test_cache_put_and_get(self):
        """Test basic cache put and get."""
        cache = TranslationCache()
        cache.put("Hello", "fr", "Bonjour")
        result = cache.get("Hello", "fr")
        assert result == "Bonjour"

    def test_cache_miss(self):
        """Test cache miss."""
        cache = TranslationCache()
        result = cache.get("Hello", "fr")
        assert result is None

    def test_cache_eviction_lru(self):
        """Test LRU eviction when cache is full."""
        cache = TranslationCache(max_size=2)
        cache.put("a", "en", "1")
        cache.put("b", "en", "2")
        cache.get("a", "en")  # Access 'a' to make it recent
        cache.put("c", "en", "3")  # Should evict 'b' (least recent)
        assert cache.get("a", "en") == "1"
        assert cache.get("b", "en") is None  # Evicted
        assert cache.get("c", "en") == "3"

    def test_cache_ttl_expiry(self):
        """Test cache entry expiry."""
        cache = TranslationCache(ttl=1)
        cache.put("Hello", "fr", "Bonjour")
        assert cache.get("Hello", "fr") == "Bonjour"
        time.sleep(1.1)
        assert cache.get("Hello", "fr") is None  # Expired

    def test_cache_clear(self):
        """Test cache clear."""
        cache = TranslationCache()
        cache.put("Hello", "fr", "Bonjour")
        cache.clear()
        assert cache.get("Hello", "fr") is None
        stats = cache.stats()
        assert stats["hits"] == 0
        # Misses counter is not reset by clear() since get() increments it

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = TranslationCache()
        cache.put("Hello", "fr", "Bonjour")
        cache.get("Hello", "fr")  # Hit
        cache.get("World", "fr")  # Miss
        stats = cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["size"] == 1
        assert stats["hit_rate"] == 0.5

    def test_cache_different_languages(self):
        """Test caching with different languages."""
        cache = TranslationCache()
        cache.put("Hello", "fr", "Bonjour")
        cache.put("Hello", "de", "Hallo")
        assert cache.get("Hello", "fr") == "Bonjour"
        assert cache.get("Hello", "de") == "Hallo"

    def test_get_cache(self):
        """Test global cache instance."""
        cache = get_cache()
        assert isinstance(cache, TranslationCache)
        # Should return same instance
        cache2 = get_cache()
        assert cache is cache2
