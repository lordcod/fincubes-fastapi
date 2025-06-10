from config import REDIS_URL
import redis.asyncio as redis

pool = redis.ConnectionPool.from_url(REDIS_URL)
client = redis.Redis.from_pool(pool)
