"""Shared LRU cache for API search clients."""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class APICache:
    """Simple LRU cache for API search results."""

    def __init__(self, max_size: int = 128) -> None:
        self._cache: Dict[str, List[Dict[str, Any]]] = {}
        self._max_size = max_size

    def get(self, query: str, limit: int) -> Optional[List[Dict[str, Any]]]:
        """Get cached results for query, or None if not cached."""
        key = self._make_key(query, limit)
        if key in self._cache:
            # Move to end for true LRU behavior
            self._cache[key] = self._cache.pop(key)
            logger.debug(f"Cache hit for: '{query}'")
            return self._cache[key]
        return None

    def put(self, query: str, limit: int, results: List[Dict[str, Any]]) -> None:
        """Store results with LRU eviction when full."""
        key = self._make_key(query, limit)

        if len(self._cache) >= self._max_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            logger.debug(f"Cache full, evicted key: {oldest_key}")

        self._cache[key] = results
        logger.debug(f"Cached results for: '{query}' (size: {len(self._cache)})")

    def clear(self) -> None:
        """Clear all cached results."""
        self._cache.clear()
        logger.info("API cache cleared")

    @staticmethod
    def _make_key(query: str, limit: int) -> str:
        """Generate cache key from query and limit."""
        key_str = f"{query.lower()}:{limit}"
        return hashlib.sha256(key_str.encode(), usedforsecurity=False).hexdigest()[:32]
