
from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

from app.core.config import settings
from app.core.config.tortoise_orm import TORTOISE_ORM


def register_db(app: FastAPI):
    register_tortoise(
        app,
        config=TORTOISE_ORM,
        generate_schemas=True,
        add_exception_handlers=True,
    )
