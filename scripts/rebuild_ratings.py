"""Rebuild athlete ranking documents from current PostgreSQL results."""

import asyncio

from tortoise import Tortoise

from app.repositories.ratings import update_ratings
from app.shared.clients.mongodb import db


async def run() -> None:
    from app.core.config.tortoise_orm import TORTOISE_ORM

    await Tortoise.init(config=TORTOISE_ORM)
    try:
        await update_ratings(db["ranking"])
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(run())
