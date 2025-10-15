import logging
from contextlib import asynccontextmanager

import aiohttp
from fastapi import FastAPI

from app.jobs.manager import shutdown_scheduler, start_scheduler
from app.jobs.fix_resolved_time_column import fix_resolved_time_column
from app.shared.clients import session
from app.shared.clients import redis, mongodb

_log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _log.info("Starting application lifespan...")

    _log.info('Create db column...')
    await fix_resolved_time_column()

    await redis.client.ping()
    app.state.redis = redis.client
    _log.info("Connected to Redis.")

    _log.debug("Creating aiohttp session...")
    session.session = aiohttp.ClientSession()

    await mongodb.client.admin.command('ping')
    app.state.mongodb_client = mongodb.client
    app.state.mongodb_db = mongodb.db
    _log.info("Connected to MongoDB.")

    _log.debug("Starting scheduler...")
    start_scheduler()

    _log.info("Startup complete.")
    yield
    _log.info("Shutting down application...")

    _log.debug("Closing Redis...")
    await redis.client.aclose()

    _log.debug("Closing MongoDB...")
    mongodb.client.close()

    _log.debug("Closing aiohttp session...")
    await session.session.close()

    _log.debug("Shutting down scheduler...")
    shutdown_scheduler()

    _log.info("Shutdown complete.")
