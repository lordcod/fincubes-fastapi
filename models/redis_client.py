from contextlib import asynccontextmanager
import logging
from os import getenv
from fastapi import FastAPI
import redis.asyncio as redis

pool = redis.ConnectionPool.from_url(getenv("REDIS_URL"))
client = redis.Redis.from_pool(pool)
_log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await client.ping()
    app.state.redis = client
    _log.info("✅ Redis подключён")

    yield

    await client.close()
    _log.info("🛑 Redis отключён")
