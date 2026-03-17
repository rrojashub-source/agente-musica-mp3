"""
Tests for API cache module — src/api/_cache.py

Covers: cache hit, LRU eviction, clear, key generation.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from api._cache import APICache  # noqa: E402


class TestAPICacheGet:
    """Test cache get (hit and miss)"""

    def test_cache_miss_returns_none(self):
        """get() returns None for uncached query"""
        cache = APICache()
        assert cache.get("uncached", 10) is None

    def test_cache_hit_returns_results(self):
        """get() returns stored results on cache hit"""
        cache = APICache()
        data = [{"id": 1, "title": "Song A"}]
        cache.put("test query", 10, data)
        result = cache.get("test query", 10)
        assert result == data

    def test_different_limit_is_cache_miss(self):
        """Same query with different limit is a separate cache entry"""
        cache = APICache()
        cache.put("query", 5, [{"a": 1}])
        assert cache.get("query", 10) is None


class TestAPICachePut:
    """Test cache put with LRU eviction"""

    def test_put_stores_results(self):
        """put() stores results that can be retrieved"""
        cache = APICache()
        cache.put("q", 5, [{"x": 1}])
        assert cache.get("q", 5) == [{"x": 1}]

    def test_lru_eviction_when_full(self):
        """When cache is full, oldest entry is evicted"""
        cache = APICache(max_size=2)
        cache.put("first", 5, [{"id": 1}])
        cache.put("second", 5, [{"id": 2}])
        # Cache is now full (2/2)
        cache.put("third", 5, [{"id": 3}])
        # "first" should have been evicted
        assert cache.get("first", 5) is None
        assert cache.get("second", 5) == [{"id": 2}]
        assert cache.get("third", 5) == [{"id": 3}]


class TestAPICacheClear:
    """Test cache clear"""

    def test_clear_removes_all_entries(self):
        """clear() empties the cache"""
        cache = APICache()
        cache.put("a", 5, [{"id": 1}])
        cache.put("b", 5, [{"id": 2}])
        cache.clear()
        assert cache.get("a", 5) is None
        assert cache.get("b", 5) is None


class TestAPICacheMakeKey:
    """Test key generation"""

    def test_same_input_same_key(self):
        """Same query+limit produce the same cache key"""
        k1 = APICache._make_key("test", 10)
        k2 = APICache._make_key("test", 10)
        assert k1 == k2

    def test_case_insensitive(self):
        """Keys are case-insensitive (lowered before hashing)"""
        k1 = APICache._make_key("Test", 10)
        k2 = APICache._make_key("test", 10)
        assert k1 == k2

    def test_different_limit_different_key(self):
        """Different limits produce different keys"""
        k1 = APICache._make_key("test", 5)
        k2 = APICache._make_key("test", 10)
        assert k1 != k2
