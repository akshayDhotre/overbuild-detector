from typing import Any, cast

from cachetools import TTLCache  # type: ignore[import-untyped]

from overbuild.config import settings

_cache: TTLCache[str, list[Any]] = TTLCache(maxsize=1024, ttl=settings.cache_ttl_seconds)


def get_cached(key: str) -> list[Any] | None:
    return cast(list[Any] | None, _cache.get(key))


def set_cached(key: str, value: list[Any]) -> None:
    _cache[key] = value


def clear_cache() -> None:
    _cache.clear()
