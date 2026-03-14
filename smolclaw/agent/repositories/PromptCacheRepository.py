"""Prompt and result caching for expensive operations.

This module provides in-memory caching for expensive operations like vision
analysis and LLM scoring, with TTL-based expiration.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class CacheEntry:
    """Cached prompt/result entry.

    Attributes:
        key: Unique cache key
        value: Cached value
        created_at: Timestamp when entry was created
        ttl_seconds: Time-to-live in seconds
        hits: Number of cache hits
    """
    key: str
    value: Any
    created_at: float
    ttl_seconds: int
    hits: int = 0

    def is_expired(self) -> bool:
        """Check if this entry has expired.

        Returns:
            True if expired, False otherwise
        """
        return time.time() > self.created_at + self.ttl_seconds

    def touch(self) -> None:
        """Increment hit counter."""
        self.hits += 1


class PromptCacheRepository:
    """In-memory cache for expensive operations (vision, LLM scoring).

    Provides TTL-based caching with automatic expiration and cache statistics.

    Attributes:
        default_ttl_seconds: Default TTL for cache entries
    """

    def __init__(self, default_ttl_seconds: int = 300) -> None:
        """Initialize the prompt cache.

        Args:
            default_ttl_seconds: Default time-to-live for cache entries
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl_seconds

    def _make_key(self, operation: str, **kwargs: Any) -> str:
        """Create cache key from operation name and parameters.

        Args:
            operation: Operation name
            **kwargs: Operation parameters

        Returns:
            SHA256 hash of operation data (first 16 chars)
        """
        key_data = json.dumps({"op": operation, "params": kwargs}, sort_keys=True)
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]

    def get(self, operation: str, **kwargs: Any) -> Optional[Any]:
        """Get cached value if available and not expired.

        Args:
            operation: Operation name
            **kwargs: Operation parameters used in cache key

        Returns:
            Cached value if found and not expired, None otherwise
        """
        key = self._make_key(operation, **kwargs)
        entry = self._cache.get(key)
        if entry is None:
            return None
        if entry.is_expired():
            del self._cache[key]
            return None
        entry.touch()
        return entry.value

    def set(
        self,
        operation: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """Cache a value with the given TTL.

        Args:
            operation: Operation name
            value: Value to cache
            ttl_seconds: Time-to-live in seconds (uses default if None)
            **kwargs: Operation parameters used in cache key

        Returns:
            Cache key for the cached value
        """
        key = self._make_key(operation, **kwargs)
        self._cache[key] = CacheEntry(
            key=key,
            value=value,
            created_at=time.time(),
            ttl_seconds=ttl_seconds or self._default_ttl,
        )
        return key

    def delete(self, operation: str, **kwargs: Any) -> bool:
        """Delete a cached value.

        Args:
            operation: Operation name
            **kwargs: Operation parameters used in cache key

        Returns:
            True if entry was deleted, False if not found
        """
        key = self._make_key(operation, **kwargs)
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()

    def cleanup_expired(self) -> int:
        """Remove all expired entries.

        Returns:
            Number of entries removed
        """
        expired_keys = [
            key for key, entry in self._cache.items() if entry.is_expired()
        ]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)

    def stats(self) -> Dict[str, Any]:
        """Return cache statistics.

        Returns:
            Dictionary with cache statistics:
            - active_entries: Number of non-expired entries
            - total_hits: Total cache hits across all entries
            - memory_entries: Total entries in memory
        """
        now = time.time()
        active = sum(
            1 for e in self._cache.values() if now <= e.created_at + e.ttl_seconds
        )
        total_hits = sum(e.hits for e in self._cache.values())
        return {
            "active_entries": active,
            "total_hits": total_hits,
            "memory_entries": len(self._cache),
        }

    def size(self) -> int:
        """Return the number of entries in the cache.

        Returns:
            Number of cache entries
        """
        return len(self._cache)


# Global cache instance
_prompt_cache: Optional[PromptCacheRepository] = None


def get_prompt_cache() -> PromptCacheRepository:
    """Get or create the global prompt cache.

    Returns:
        Global PromptCacheRepository instance
    """
    global _prompt_cache
    if _prompt_cache is None:
        _prompt_cache = PromptCacheRepository(default_ttl_seconds=300)
    return _prompt_cache


def reset_prompt_cache() -> PromptCacheRepository:
    """Reset and return the global prompt cache.

    Returns:
        New PromptCacheRepository instance
    """
    global _prompt_cache
    _prompt_cache = PromptCacheRepository(default_ttl_seconds=300)
    return _prompt_cache


__all__ = [
    "CacheEntry",
    "PromptCacheRepository",
    "get_prompt_cache",
    "reset_prompt_cache",
]
