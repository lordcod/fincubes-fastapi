import pickle
import zlib
from typing import Any, Optional

from redis.asyncio import Redis


class RedisCachePickleCompressed:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def set(self, key: str, value: Any, expire_seconds: Optional[int] = None):
        data = pickle.dumps(value)
        compressed = zlib.compress(data)
        await self.redis.set(key, compressed, ex=expire_seconds)

    async def get(self, key: str) -> Optional[Any]:
        compressed = await self.redis.get(key)
        if compressed is None:
            return None
        data = zlib.decompress(compressed)
        return pickle.loads(data)
