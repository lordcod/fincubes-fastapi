import hashlib
from datetime import date
from typing import Optional

from tortoise import Tortoise

from app.repositories.temp import build_top_results_query, compile_query_with_dollar_params
from app.shared.cache.redis_compressed import RedisCachePickleCompressed
from app.shared.clients.redis import client


async def get_top_results(
    distance: Optional[int] = None,
    stroke: Optional[str] = None,
    gender: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    season: Optional[int] = None,
    current_season: Optional[bool] = False,
):
    cache = RedisCachePickleCompressed(client)
    cache_key_raw = f"{stroke}:{distance}:{gender}:{limit}:{offset}:{min_age}:{max_age}:{season}:{current_season}"
    cache_key = "top_results:" + \
        hashlib.sha256(cache_key_raw.encode()).hexdigest()
    cached = await cache.get(cache_key)
    if cached:
        return cached

    query = build_top_results_query(
        stroke=stroke,
        distance=distance,
        gender=gender,
        min_age=min_age,
        max_age=max_age,
        season=season,
        offset=offset,
        limit=limit,
    )
    sql, params = compile_query_with_dollar_params(query)

    results = await Tortoise.get_connection(
        "default").execute_query_dict(
            sql, params)
    await cache.set(cache_key, results, expire_seconds=60 * 60)
    return results
