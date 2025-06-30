import redis.asyncio as redis

from app.core.config import settings

pool = redis.ConnectionPool.from_url(settings.REDIS_URL)
client = redis.Redis.from_pool(pool)
