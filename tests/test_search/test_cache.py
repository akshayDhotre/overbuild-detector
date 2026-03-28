import time

from cachetools import TTLCache

from overbuild.search import cache


def test_cache_set_get_and_clear() -> None:
    cache.set_cached("k", [1, 2, 3])
    assert cache.get_cached("k") == [1, 2, 3]
    cache.clear_cache()
    assert cache.get_cached("k") is None


def test_cache_ttl_expiry(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    temp_cache = TTLCache(maxsize=4, ttl=0.01)
    monkeypatch.setattr(cache, "_cache", temp_cache)
    cache.set_cached("k", [1])
    assert cache.get_cached("k") == [1]
    time.sleep(0.02)
    assert cache.get_cached("k") is None
