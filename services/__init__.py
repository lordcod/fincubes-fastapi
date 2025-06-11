from contextlib import asynccontextmanager
import aiohttp
from fastapi import FastAPI
from models.redis_client import client
from . import s3_session
from services.backgrounds import start_scheduler, shutdown_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    await client.ping()
    app.state.redis = client
    s3_session.session = aiohttp.ClientSession()
    start_scheduler()

    yield

    await client.close()
    await s3_session.session.close()
    shutdown_scheduler()
