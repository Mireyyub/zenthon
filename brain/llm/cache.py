"""
Leon LLM Cache — High-Performance v0.9

In-memory LRU cache with TTL support for:
  - LLM completions (prompt → response)
  - Embeddings (text → vector)
  - RAG retrieval results (query → context)

Features:
  - Thread-safe & async-safe
  - Configurable TTL per cache type
  - Size-based eviction (LRU)
  - Hit/miss metrics
"""

from __future__ import annotations

import hashlib
import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from functools import wraps
from collections import OrderedDict
import threading

from core.logger import logger


@dataclass
class CacheEntry:
    value: Any
    created_at: float
    ttl: float
    hits: int = 0


class LRUCache:
    """Thread-safe LRU cache with TTL."""

    def __init__(self, maxsize: int = 128, default_ttl: float = 300.0):
        self.maxsize = maxsize
        self.default_ttl = default_ttl
        self._store: OrderedDict = OrderedDict()
        self._lock = threading.RLock()
        self._metrics: Dict[str, int] = {"hits": 0, "misses": 0, "evictions": 0}

    def _make_key(self, *args: Any, **kwargs: Any) -> str:
        key_data = f"{args}:{sorted(kwargs.items())}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:32]

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._metrics["misses"] += 1
                return None
            if time.time() - entry.created_at > entry.ttl:
                del self._store[key]
                self._metrics["misses"] += 1
                return None
            self._store.move_to_end(key)
            entry.hits += 1
            self._metrics["hits"] += 1
            return entry.value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        with self._lock:
            if key in self._store:
                del self._store[key]
            while len(self._store) >= self.maxsize:
                self._store.popitem(last=False)
                self._metrics["evictions"] += 1
            self._store[key] = CacheEntry(
                value=value,
                created_at=time.time(),
                ttl=ttl if ttl is not None else self.default_ttl,
            )

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def keys(self) -> List[str]:
        with self._lock:
            return list(self._store.keys())

    def metrics(self) -> Dict[str, Any]:
        with self._lock:
            total = self._metrics["hits"] + self._metrics["misses"]
            return {
                **self._metrics,
                "size": len(self._store),
                "hit_rate": (self._metrics["hits"] / total) if total else 0.0,
            }

    def cached(self, ttl: Optional[float] = None, key_fn: Optional[Callable] = None):
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                key = key_fn(*args, **kwargs) if key_fn else self._make_key(*args, **kwargs)
                hit = self.get(key)
                if hit is not None:
                    return hit
                result = func(*args, **kwargs)
                self.set(key, result, ttl=ttl)
                return result

            return wrapper

        return decorator


_completion_cache = LRUCache(maxsize=256, default_ttl=120.0)
_embedding_cache = LRUCache(maxsize=512, default_ttl=3600.0)
_rag_cache = LRUCache(maxsize=128, default_ttl=60.0)


def get_completion_cache() -> LRUCache:
    return _completion_cache


def get_embedding_cache() -> LRUCache:
    return _embedding_cache


def get_rag_cache() -> LRUCache:
    return _rag_cache


def cache_metrics() -> Dict[str, Any]:
    return {
        "completion": _completion_cache.metrics(),
        "embedding": _embedding_cache.metrics(),
        "rag": _rag_cache.metrics(),
    }


def cache_clear_all() -> None:
    _completion_cache.clear()
    _embedding_cache.clear()
    _rag_cache.clear()
