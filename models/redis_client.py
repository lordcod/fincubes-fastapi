from os import getenv
import redis.asyncio as redis

pool = redis.ConnectionPool.from_url(getenv("REDIS_URL"))
client = redis.Redis.from_pool(pool)
