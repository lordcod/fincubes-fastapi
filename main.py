import logging
import sys
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
import uvicorn
from config import DATABASE_URL
from routers import competitions, distances, results, athletes, top_recent, auth
from tortoise.contrib.fastapi import register_tortoise
from models.redis_client import lifespan

app = FastAPI(
    title="Swimming API",
    lifespan=lifespan
)

dev_mode = sys.platform == 'win32'
logger = logging.getLogger(__name__)

if dev_mode:
    logger.info("Start app in dev mode")
    origins = ['*']
else:
    origins = ['https://fincubes.ru']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
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
    uvicorn.run(
        app,
        port=5000
    )
