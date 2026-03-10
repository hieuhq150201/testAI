"""
⚡ Agent-D2: In-memory LRU Cache
Giảm redundant computation cho repeated requests
"""
from collections import OrderedDict
import hashlib, time, threading

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

    @property
    def stats(self):
        total = self.hits + self.misses
        return {
            "size": len(self._cache),
            "maxsize": self._maxsize,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hits / total, 4) if total > 0 else 0.0
        }

prediction_cache = LRUCache(maxsize=1000)
