import logging
from platform import release
import sys
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
import uvicorn
from config import DATABASE_URL
from routers import competitions, distances, results, athletes, top_recent, auth
from tortoise.contrib.fastapi import register_tortoise
from models.redis_client import lifespan
from starlette.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI(
    title="Swimming API",
    lifespan=lifespan
)

dev_mode = sys.platform == 'win32'
logger = logging.getLogger(__name__)

if dev_mode:
    logger.info("Start app in dev mode")
    origins = ['*']
    allowed_hosts = ["*"]
else:
    origins = ['https://fincubes.ru']
    allowed_hosts = ["localhost", "127.0.0.1", "fincubes.ru", "*.fincubes.ru"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=allowed_hosts
)

app.include_router(competitions.router)
app.include_router(results.router)
app.include_router(athletes.router)
app.include_router(distances.router)
app.include_router(top_recent.router)
app.include_router(auth.router)


register_tortoise(
    app,
    db_url=DATABASE_URL,
    modules={"models": ["models.models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)


if __name__ == '__main__':
    if dev_mode:
        # uvicorn main:app  --reload --host 0.0.0.0 --port 8000 --ssl-keyfile localhost-key.pem --ssl-certfile localhost.pem

        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            ssl_keyfile="localhost-key.pem",
            ssl_certfile="localhost.pem",
        )
    else:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
        )
