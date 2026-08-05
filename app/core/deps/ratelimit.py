from fastapi import Depends
from redis.asyncio import Redis as RedisClient

from app.core.config import settings
from app.core.deps.redis import get_redis
from app.core.errors import APIError, ErrorCode


REQUEST_RATE_LIMIT_INTERVAL_SECONDS = 60
REQUEST_RATE_LIMIT_COUNT = 300

CHALLENGE_RATE_LIMIT_INTERVAL_SECONDS = 60
CHALLENGE_RATE_LIMIT_COUNT = 60

TOKEN_RATE_LIMIT_INTERVAL_SECONDS = 60
TOKEN_RATE_LIMIT_COUNT = 30

AVATAR_UPLOAD_RATE_LIMIT_INTERVAL_SECONDS = 60 * 60
AVATAR_UPLOAD_RATE_LIMIT_COUNT = 20

EMAIL_CODE_RATE_LIMIT_INTERVAL_SECONDS = 10 * 60
EMAIL_CODE_RATE_LIMIT_COUNT = 3

PASSWORD_RESET_RATE_LIMIT_INTERVAL_SECONDS = 10 * 60
PASSWORD_RESET_RATE_LIMIT_COUNT = 3


async def enforce_rate_limit(
    redis: RedisClient,
    *,
    name: str,
    key: str,
    interval: int,
    count: int,
):
    if settings.IGNORE_RATE_LIMIT:
        return

    redis_key = f"ratelimit:{name}:{key}"

    attempts = await redis.incr(redis_key)
    if attempts == 1:
        await redis.expire(redis_key, interval)

    if attempts > count:
        raise APIError(ErrorCode.RATE_LIMIT_EXCEEDED)


def create_ratelimit(name: str, interval: int, count: int = 1):
    async def wrapped(redis: RedisClient = Depends(get_redis)):
        async def active(key):
            await enforce_rate_limit(
                redis,
                name=name,
                key=str(key),
                interval=interval,
                count=count,
            )

        return active

    return wrapped
