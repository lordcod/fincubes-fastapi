import asyncio
import redis.asyncio as redis
import asyncio
from tortoise import Tortoise, fields
from tortoise.models import Model
from fastapi import FastAPI

from config import DATABASE_URL, TORTOISE_ORM
from models.models import Athlete, Distance, Result
from utils.sql_raw import get_top_results

RESULTS_SCRIPT_SHA = "d12da792be2c46ec8982fbb45697584f545a9610"


async def get_rank(client, gender, stroke, distance, time):
    time = (
        time.hour * 60 * 60
        + time.minute * 60
        + time.second
        + ((time.microsecond // 1000)/1000)
    )
    rank = await client.evalsha(RESULTS_SCRIPT_SHA, 1,
                                f"top:{gender}:{stroke}:{distance}",
                                time)
    return rank


async def load_tortoise():
    await Tortoise.init(
        db_url=DATABASE_URL,
        modules={"models": ["models.models"]},
    )
    await Tortoise.generate_schemas()


async def close_tortoise():
    await Tortoise.close_connections()


async def main():
    await load_tortoise()
    pool = redis.ConnectionPool.from_url("redis://localhost")
    client = redis.Redis.from_pool(pool)

    results = await Result.all().prefetch_related("athlete")
    for result in results:
        if not result.result:
            continue
        rank = await get_rank(client, result.athlete.gender, result.stroke, result.distance, result.result)
        if result.final:
            final_rank = await get_rank(client, result.athlete.gender, result.stroke, result.distance, result.final)
    await client.aclose()
    await close_tortoise()


if __name__ == '__main__':
    asyncio.run(main())
