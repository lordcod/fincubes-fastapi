import logging
from contextlib import asynccontextmanager

import aiohttp
from fastapi import FastAPI

from app.jobs.daily_ranking import shutdown_scheduler, start_scheduler
from app.jobs.fix_resolved_time_column import fix_resolved_time_column
from app.shared.clients import session
from app.shared.clients.redis import client, settings

_log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _log.info("Starting application lifespan...")

    _log.info('Create db column...')
    await fix_resolved_time_column()

    _log.debug("Pinging Redis %s...", settings.REDIS_URL)
    await client.ping()
    app.state.redis = client
    _log.info("Connected to Redis.")

    _log.debug("Creating aiohttp session...")
    session.session = aiohttp.ClientSession()

    _log.debug("Starting scheduler...")
    start_scheduler()

    _log.info("Startup complete.")
    yield
    _log.info("Shutting down application...")

    _log.debug("Closing Redis...")
    await client.aclose()

    _log.debug("Closing aiohttp session...")
    await session.session.close()

    _log.debug("Shutting down scheduler...")
    shutdown_scheduler()

    _log.info("Shutdown complete.")
