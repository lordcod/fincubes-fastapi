import logging
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastfsx import FileRouter

from app.core.logger import setup_logging
from app.core.startup.database import register_db
from app.core.startup.exception_handler import add_exception_handler
from app.core.startup.lifespan import lifespan
from app.core.startup.middleware import add_middleware
from app.core.startup.tokens import init_jwt

PAGES_DIR = Path(os.getcwd()) / 'app' / 'pages'
_log = logging.getLogger(__name__)


def create_app(env_mode: str = 'dev') -> FastAPI:
    app = FastAPI(title="FinCubes API", lifespan=lifespan)
    app.include_router(FileRouter(PAGES_DIR).build())

    _log.debug("Registering database...")
    register_db(app)

    _log.debug("Adding exception handlers...")
    add_exception_handler(app)

    _log.debug("Adding middleware...")
    add_middleware(app, env_mode)

    _log.debug("Init jwt tokens...")
    init_jwt()

    return app


def start():
    setup_logging()
    _log.info("[PROD] Starting FinCubes API...")
    uvicorn.run(
        create_app(env_mode='prod'),
        host="0.0.0.0",
        port=8000,
        # ssl_keyfile="localhost-key.pem" if sys.platform == "win32" else None,
        # ssl_certfile="localhost.pem" if sys.platform == "win32" else None,
        log_level=None,
        access_log=None,
        log_config=None,
    )


def dev():
    setup_logging()
    _log.info("[DEV] Starting FinCubes API...")
    uvicorn.run(
        "app.main:create_app",
        factory=True,
        reload=True,
        host="0.0.0.0",
        port=8000,
        log_config="app/core/config/log_config.json",
    )
