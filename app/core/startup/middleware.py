from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import middleware_settings


def add_middleware(app: FastAPI):
    if middleware_settings.dev_mode:
        origins = middleware_settings.dev_origins
        allowed_hosts = middleware_settings.dev_hosts
        app.servers = [middleware_settings.local_server]
    else:
        origins = middleware_settings.prod_origins
        allowed_hosts = middleware_settings.prod_hosts

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=allowed_hosts,
    )
