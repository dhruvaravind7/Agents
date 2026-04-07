import os
import time
from dotenv import load_dotenv

load_dotenv()

_TTL = int(os.getenv("CACHE_TTL_SECONDS", "300"))


class TTLCache:
    def __init__(self, ttl=_TTL):
        self._ttl = ttl
        self._store: dict[str, tuple[object, float]] = {}

    def get(self, key):
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.monotonic() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key, value):
        self._store[key] = (value, time.monotonic() + self._ttl)


cache = TTLCache()
