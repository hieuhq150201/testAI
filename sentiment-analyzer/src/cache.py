"""
⚡ Sprint 6 — Smart Cache: Redis nếu available, fallback LRU in-memory
"""
from collections import OrderedDict
import hashlib, threading, logging, os

log = logging.getLogger(__name__)

class LRUCache:
    def __init__(self, maxsize=1000):
        self._cache = OrderedDict()
        self._maxsize = maxsize
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def _key(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()

    def get(self, text: str):
        key = self._key(text)
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                self.hits += 1
                return self._cache[key]
            self.misses += 1
            return None

    def set(self, text: str, value: dict):
        key = self._key(text)
        with self._lock:
            self._cache[key] = value
            self._cache.move_to_end(key)
            if len(self._cache) > self._maxsize:
                self._cache.popitem(last=False)

    def clear(self):
        with self._lock:
            self._cache.clear()
            self.hits = self.misses = 0

    @property
    def stats(self):
        total = self.hits + self.misses
        return {
            "backend": "lru_memory",
            "size": len(self._cache),
            "maxsize": self._maxsize,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hits / total, 4) if total > 0 else 0.0
        }


class RedisCache:
    """Redis-backed cache với JSON serialization. TTL = 1 giờ."""
    def __init__(self, host="localhost", port=6379, ttl=3600):
        import redis, json
        self._redis = redis.Redis(host=host, port=port, decode_responses=True)
        self._ttl = ttl
        self._json = json
        self.hits = 0
        self.misses = 0

    def _key(self, text: str) -> str:
        return f"sentiment:{hashlib.md5(text.encode()).hexdigest()}"

    def get(self, text: str):
        try:
            val = self._redis.get(self._key(text))
            if val:
                self.hits += 1
                return self._json.loads(val)
            self.misses += 1
            return None
        except Exception:
            self.misses += 1
            return None

    def set(self, text: str, value: dict):
        try:
            self._redis.setex(self._key(text), self._ttl, self._json.dumps(value))
        except Exception:
            pass

    def clear(self):
        try:
            keys = self._redis.keys("sentiment:*")
            if keys: self._redis.delete(*keys)
        except Exception:
            pass

    @property
    def stats(self):
        total = self.hits + self.misses
        try:
            size = len(self._redis.keys("sentiment:*"))
        except Exception:
            size = -1
        return {
            "backend": "redis",
            "size": size,
            "ttl_sec": self._ttl,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hits / total, 4) if total > 0 else 0.0
        }


def create_cache():
    """Auto-detect Redis → fallback LRU"""
    redis_url = os.getenv("REDIS_URL", "")
    if redis_url:
        try:
            import redis
            host, port = (redis_url.split(":")[-2].lstrip("/"),
                          int(redis_url.split(":")[-1]))
            c = RedisCache(host=host, port=port)
            c._redis.ping()
            log.info("✅ Using Redis cache")
            return c
        except Exception as e:
            log.warning(f"⚠️  Redis unavailable ({e}), falling back to LRU")

    log.info("📦 Using LRU in-memory cache")
    return LRUCache(maxsize=1000)


prediction_cache = create_cache()
