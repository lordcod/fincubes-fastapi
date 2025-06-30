from fastapi import Depends
from redis.asyncio import Redis as RedisClient

from app.core.deps.redis import get_redis
from app.core.errors import APIError, ErrorCode


def create_ratelimit(name: str, interval: int, count: int = 1):
    async def wrapped(redis: RedisClient = Depends(get_redis)):
        async def active(key):
            key = f"ratelimit:{name}:{key}"

            attempts = await redis.get(key)
            if attempts is None:
                await redis.set(key, 1, ex=interval)
                return

            if int(attempts) >= count:
                raise APIError(ErrorCode.RATE_LIMIT_EXCEEDED)
            await redis.incrby(key, 1)

        return active

    return wrapped
