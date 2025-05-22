
from datetime import datetime
from fastapi import Depends, HTTPException
from redis.asyncio import Redis as RedisClient

from models.deps import get_redis


def create_ratelimit(name: str, interval: int):
    async def wrapped(
        redis: RedisClient = Depends(get_redis)
    ):
        async def active(key):
            key = f"ratelimit:{name}:{key}"
            now = datetime.now().timestamp()
            last_upload_timestamp = await redis.get(key)
            if last_upload_timestamp:
                last = float(last_upload_timestamp)
                if now - last < interval:
                    raise HTTPException(
                        status_code=429,
                        detail="Действуют ограничения, повторите попытку позже.")
            await redis.set(key, now)
        return active

    return wrapped
