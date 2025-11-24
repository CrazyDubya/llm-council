"""Response caching layer for LLM Council.

Provides in-memory LRU caching with TTL support and statistics tracking.
Redis-ready interface for future scaling.
"""

import hashlib
import json
import time
from typing import Any, Dict, Optional, List
from collections import OrderedDict
from dataclasses import dataclass, asdict
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """A single cache entry with metadata."""
    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int
    ttl: float  # Time-to-live in seconds


@dataclass
class CacheStats:
    """Cache statistics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_requests: int = 0
    current_size: int = 0
    max_size: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return (self.hits / self.total_requests) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            **asdict(self),
            'hit_rate': round(self.hit_rate, 2)
        }


class LRUCache:
    """
    LRU (Least Recently Used) cache with TTL support.

    Features:
    - Maximum size limit with LRU eviction
    - Time-to-live (TTL) for entries
    - Statistics tracking (hits, misses, evictions)
    - Thread-safe with async locks
    - Redis-ready interface (can be swapped with Redis implementation)
    """

    def __init__(self, max_size: int = 1000, default_ttl: float = 86400):
        """
        Initialize the cache.

        Args:
            max_size: Maximum number of entries to store
            default_ttl: Default time-to-live in seconds (default: 24 hours)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()
        self._stats = CacheStats(max_size=max_size)

    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found and not expired, None otherwise
        """
        async with self._lock:
            self._stats.total_requests += 1

            entry = self._cache.get(key)

            if entry is None:
                self._stats.misses += 1
                logger.debug(f"Cache MISS: {key}")
                return None

            # Check if entry has expired
            if self._is_expired(entry):
                logger.debug(f"Cache EXPIRED: {key}")
                del self._cache[key]
                self._stats.current_size -= 1
                self._stats.misses += 1
                return None

            # Update access metadata
            entry.last_accessed = time.time()
            entry.access_count += 1

            # Move to end (most recently used)
            self._cache.move_to_end(key)

            self._stats.hits += 1
            logger.debug(f"Cache HIT: {key}")
            return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None
    ) -> None:
        """
        Store a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        async with self._lock:
            now = time.time()
            ttl = ttl if ttl is not None else self.default_ttl

            # If key exists, update it
            if key in self._cache:
                entry = self._cache[key]
                entry.value = value
                entry.created_at = now
                entry.last_accessed = now
                entry.ttl = ttl
                self._cache.move_to_end(key)
                logger.debug(f"Cache UPDATE: {key}")
                return

            # Evict least recently used if at capacity
            if len(self._cache) >= self.max_size:
                evicted_key, _ = self._cache.popitem(last=False)
                self._stats.evictions += 1
                self._stats.current_size -= 1
                logger.debug(f"Cache EVICT: {evicted_key}")

            # Create new entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                last_accessed=now,
                access_count=0,
                ttl=ttl
            )

            self._cache[key] = entry
            self._stats.current_size += 1
            logger.debug(f"Cache SET: {key}")

    async def delete(self, key: str) -> bool:
        """
        Delete a key from the cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key was deleted, False if not found
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats.current_size -= 1
                logger.debug(f"Cache DELETE: {key}")
                return True
            return False

    async def clear(self) -> None:
        """Clear all entries from the cache."""
        async with self._lock:
            self._cache.clear()
            self._stats.current_size = 0
            logger.info("Cache CLEARED")

    async def cleanup_expired(self) -> int:
        """
        Remove all expired entries from the cache.

        Returns:
            Number of entries removed
        """
        async with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if self._is_expired(entry)
            ]

            for key in expired_keys:
                del self._cache[key]
                self._stats.current_size -= 1

            if expired_keys:
                logger.info(f"Cache cleanup: removed {len(expired_keys)} expired entries")

            return len(expired_keys)

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if a cache entry has expired."""
        return (time.time() - entry.created_at) > entry.ttl

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        async with self._lock:
            return self._stats.to_dict()

    async def get_keys(self) -> List[str]:
        """Get all cache keys."""
        async with self._lock:
            return list(self._cache.keys())

    async def get_entry_info(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a cache entry.

        Args:
            key: Cache key

        Returns:
            Entry metadata if found, None otherwise
        """
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None

            return {
                'key': entry.key,
                'created_at': entry.created_at,
                'last_accessed': entry.last_accessed,
                'access_count': entry.access_count,
                'ttl': entry.ttl,
                'age': time.time() - entry.created_at,
                'expires_in': entry.ttl - (time.time() - entry.created_at),
                'is_expired': self._is_expired(entry)
            }


class CouncilCache:
    """
    High-level caching interface for LLM Council responses.

    Provides convenient methods for caching strategy executions with
    automatic key generation.
    """

    def __init__(self, max_size: int = 1000, default_ttl: float = 86400):
        """
        Initialize the council cache.

        Args:
            max_size: Maximum number of entries
            default_ttl: Default TTL in seconds (24 hours)
        """
        self._cache = LRUCache(max_size=max_size, default_ttl=default_ttl)

    @staticmethod
    def generate_cache_key(
        query: str,
        models: List[str],
        strategy: str,
        strategy_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a cache key for a council query.

        Args:
            query: User query
            models: List of model identifiers
            strategy: Strategy name
            strategy_config: Strategy configuration dict

        Returns:
            Cache key (SHA256 hash)
        """
        # Normalize inputs for consistent hashing
        models_sorted = sorted(models)
        config_str = json.dumps(strategy_config or {}, sort_keys=True)

        # Create a unique string representing this query
        key_data = {
            'query': query.strip().lower(),
            'models': models_sorted,
            'strategy': strategy,
            'config': config_str
        }

        # Generate hash
        key_string = json.dumps(key_data, sort_keys=True)
        hash_object = hashlib.sha256(key_string.encode())
        return f"council:{hash_object.hexdigest()}"

    async def get_response(
        self,
        query: str,
        models: List[str],
        strategy: str,
        strategy_config: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a cached response for a council query.

        Args:
            query: User query
            models: List of model identifiers
            strategy: Strategy name
            strategy_config: Strategy configuration

        Returns:
            Cached response dict if found, None otherwise
        """
        key = self.generate_cache_key(query, models, strategy, strategy_config)
        return await self._cache.get(key)

    async def set_response(
        self,
        query: str,
        models: List[str],
        strategy: str,
        response: Dict[str, Any],
        strategy_config: Optional[Dict[str, Any]] = None,
        ttl: Optional[float] = None
    ) -> str:
        """
        Cache a response for a council query.

        Args:
            query: User query
            models: List of model identifiers
            strategy: Strategy name
            response: Response dict to cache
            strategy_config: Strategy configuration
            ttl: Custom TTL (uses default if not specified)

        Returns:
            Cache key used
        """
        key = self.generate_cache_key(query, models, strategy, strategy_config)
        await self._cache.set(key, response, ttl=ttl)
        return key

    async def invalidate_query(
        self,
        query: str,
        models: List[str],
        strategy: str,
        strategy_config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Invalidate (delete) a specific cached query.

        Args:
            query: User query
            models: List of model identifiers
            strategy: Strategy name
            strategy_config: Strategy configuration

        Returns:
            True if deleted, False if not found
        """
        key = self.generate_cache_key(query, models, strategy, strategy_config)
        return await self._cache.delete(key)

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return await self._cache.get_stats()

    async def clear(self) -> None:
        """Clear all cached responses."""
        await self._cache.clear()

    async def cleanup_expired(self) -> int:
        """Remove expired entries."""
        return await self._cache.cleanup_expired()


# Global cache instance
_global_cache: Optional[CouncilCache] = None


def get_cache() -> CouncilCache:
    """
    Get the global cache instance.

    Returns:
        Global CouncilCache instance
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = CouncilCache(max_size=1000, default_ttl=86400)
    return _global_cache


async def start_cleanup_task(interval: int = 3600):
    """
    Start a background task to periodically clean up expired entries.

    Args:
        interval: Cleanup interval in seconds (default: 1 hour)
    """
    cache = get_cache()
    while True:
        await asyncio.sleep(interval)
        try:
            removed = await cache.cleanup_expired()
            if removed > 0:
                logger.info(f"Periodic cleanup: removed {removed} expired entries")
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
