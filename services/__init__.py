from contextlib import asynccontextmanager
import aiohttp
from fastapi import FastAPI
from models.redis_client import client
from . import s3_session


@asynccontextmanager
async def lifespan(app: FastAPI):
    await client.ping()
    app.state.redis = client
    s3_session.session = aiohttp.ClientSession()

    yield

    await client.close()
    await s3_session.session.close()
