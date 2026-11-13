from services.cache import clear_cache, get_cache_stats, get_cached, set_cached


def test_cache_set_and_get():
    clear_cache()
    set_cached("test_ns", "key1", {"result": 42})
    assert get_cached("test_ns", "key1") == {"result": 42}
    assert get_cached("test_ns", "non_existent") is None


def test_cache_stats():
    clear_cache()
    set_cached("test_ns", "key1", "val1")
    get_cached("test_ns", "key1")  # hit
    get_cached("test_ns", "key2")  # miss
    stats = get_cache_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["hit_ratio_percent"] == 50.0
    assert stats["namespaces"]["test_ns"] == 1


def test_cache_lru_eviction():
    clear_cache()
    # Set maxsize to 2
    set_cached("lru_ns", "k1", "v1", maxsize=2)
    set_cached("lru_ns", "k2", "v2", maxsize=2)
    # Access k1 to make it most recently used
    get_cached("lru_ns", "k1")
    # Insert k3, which should evict k2
    set_cached("lru_ns", "k3", "v3", maxsize=2)
    assert get_cached("lru_ns", "k1") == "v1"
    assert get_cached("lru_ns", "k2") is None
    assert get_cached("lru_ns", "k3") == "v3"

