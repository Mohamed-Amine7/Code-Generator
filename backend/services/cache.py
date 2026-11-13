import hashlib
import json
import logging
import threading
from collections import OrderedDict
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

_LOCK = threading.Lock()
_CACHE: Dict[str, OrderedDict] = {}
_STATS = {"hits": 0, "misses": 0}


def _make_key(*args, **kwargs) -> str:
    """Génère une clé SHA-256 stable à partir des arguments."""
    payload = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def get_cached(namespace: str, key: str) -> Optional[Any]:
    with _LOCK:
        bucket = _CACHE.get(namespace)
        if bucket is not None and key in bucket:
            # Move to end (most recently used)
            val = bucket.pop(key)
            bucket[key] = val
            _STATS["hits"] += 1
            logger.debug("Cache HIT [%s] key=%s", namespace, key[:8])
            return val
        _STATS["misses"] += 1
        return None


def set_cached(namespace: str, key: str, value: Any, maxsize: int = 500) -> None:
    with _LOCK:
        if namespace not in _CACHE:
            _CACHE[namespace] = OrderedDict()
        bucket = _CACHE[namespace]
        if key in bucket:
            bucket.pop(key)
        elif len(bucket) >= maxsize:
            bucket.popitem(last=False)  # éviction du plus ancien (LRU)
        bucket[key] = value
        logger.debug("Cache SET [%s] key=%s", namespace, key[:8])


def cached_ai(namespace: str, maxsize: int = 500):
    """Décorateur de mise en cache pour les fonctions d'analyse IA lentes."""

    def decorator(fn: Callable):
        def wrapper(*args, **kwargs):
            key = _make_key(*args, **kwargs)
            hit = get_cached(namespace, key)
            if hit is not None:
                return hit
            result = fn(*args, **kwargs)
            set_cached(namespace, key, result, maxsize=maxsize)
            return result

        return wrapper

    return decorator


def get_cache_stats() -> Dict[str, Any]:
    with _LOCK:
        total = _STATS["hits"] + _STATS["misses"]
        hit_ratio = round((_STATS["hits"] / total * 100), 1) if total > 0 else 0.0
        sizes = {ns: len(bucket) for ns, bucket in _CACHE.items()}
        return {
            "hits": _STATS["hits"],
            "misses": _STATS["misses"],
            "total_requests": total,
            "hit_ratio_percent": hit_ratio,
            "namespaces": sizes,
        }


def clear_cache() -> None:
    with _LOCK:
        _CACHE.clear()
        _STATS["hits"] = 0
        _STATS["misses"] = 0

