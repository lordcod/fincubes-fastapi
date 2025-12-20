import hashlib
from datetime import date
from typing import List, Optional

from tortoise import Tortoise

from app.repositories.sa.top_results import build_top_results_query
from app.repositories.sa.utils import compile_query_with_dollar_params, compile_query_with_literals
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
    categories: Optional[List[str]] = None,

    year: Optional[int] = None,
    season: Optional[int] = None,
    current_season: Optional[bool] = False,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,

    courses: Optional[List[str]] = None,
    statuses: Optional[List[str]] = None,
):
    cache = RedisCachePickleCompressed(client)

    cache_key_raw = (
        f"{stroke}:{distance}:{gender}:"
        f"{limit}:{offset}:"
        f"{min_age}:{max_age}:{categories}:"
        f"{year}:{season}:{current_season}:"
        f"{start_date}:{end_date}:"
        f"{courses}:{statuses}"
    )
    cache_key = "top_results:" + hashlib.sha256(
        cache_key_raw.encode()
    ).hexdigest()

    cached = await cache.get(cache_key)
    if cached:
        return cached

    query = build_top_results_query(
        stroke=stroke,
        distance=distance,
        gender=gender,
        min_age=min_age,
        max_age=max_age,
        categories=categories,
        year=year,
        season=season,
        current_season=current_season,
        start_date=start_date,
        end_date=end_date,
        courses=courses,
        statuses=statuses,
        offset=offset,
        limit=limit,
    )

    sql = compile_query_with_literals(query)
    print(sql)
    results = await Tortoise.get_connection("default").execute_query_dict(sql)

    await cache.set(cache_key, results, expire_seconds=60 * 60)
    return results
