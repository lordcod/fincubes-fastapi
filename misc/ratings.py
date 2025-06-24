import logging
from collections import defaultdict
from datetime import time

import redis.asyncio as redis
from tortoise import Tortoise

from misc.get_top_results import get_top_results
from misc.redis_cache_compressed import RedisCachePickleCompressed
from schemas.top import parse_best_full_result

_log = logging.getLogger(__name__)

BATCH_SIZE = 1000
lua_script = """
local zset_name = KEYS[1]
local score = ARGV[1]
local exists = redis.call('ZSCORE', zset_name, score)
if exists == false then
    redis.call('ZADD', zset_name, score, score)
end
return redis.call('ZRANK', zset_name, score)
"""
categories = [
    {
        "name": "Малыши",
        "id": "kids",
        "min_age": 0,
        "max_age": 9
    },
    {
        "name": "Юные",
        "id": "young",
        "min_age": 10,
        "max_age": 11
    },
    {
        "name": "Юниоры",
        "id": "junior",
        "min_age": 12,
        "max_age": 13
    },
    {
        "name": "Кадеты",
        "id": "cadet",
        "min_age": 14,
        "max_age": 15
    },
    {
        "name": "Юниоры старшие",
        "id": "junior_senior",
        "min_age": 16,
        "max_age": 17
    },
    {
        "name": "Молодёжь",
        "id": "youth",
        "min_age": 18,
        "max_age": 21
    },
    {
        "name": "Взрослые",
        "id": "adult",
        "min_age": 22,
        "max_age": 34
    },
    {
        "name": "Мастера",
        "id": "masters",
        "min_age": 35,
        "max_age": 44
    },
    {
        "name": "Легенды",
        "id": "legends",
        "min_age": 45,
        "max_age": 150
    },
    {
        "name": "Общий зачёт",
        "id": "absolute",
        "min_age": None,
        "max_age": None
    }
]


def as_duration(result: time):
    return (
        result.hour * 60 * 60
        + result.minute * 60
        + result.second
        + ((result.microsecond // 1000) / 1000)
    )


async def get_rank(
    client: redis.Redis, gender: str, stroke: str, distance: int, result_time: time
):
    result = as_duration(result_time)

    rank = await client.eval(lua_script, 1, f"top:{gender}:{stroke}:{distance}", result)
    return rank + 1


async def update_ratings(client: redis.Redis):
    _log.debug("Start updating athlete rankings")

    athlete_results = defaultdict(lambda: defaultdict(list))

    for season in [True, False]:
        for category in categories:
            _log.debug('Parse category: %s (season:%s)',
                       category['name'], season)
            results = await get_top_results(min_age=category['min_age'],
                                            max_age=category['max_age'],
                                            current_season=season)
            results = [parse_best_full_result(res) for res in results]
            for top in results:
                athlete_results[top.athlete.id][('season' if season else 'global') + ':' + category['id']
                                                ].append(top.model_dump())

    pipe = client.pipeline()
    cache = RedisCachePickleCompressed(pipe)
    for athlete_id, results in athlete_results.items():
        cache_key = f"athlete:ranking:{athlete_id}"
        await cache.set(cache_key, dict(results))
    await pipe.execute()


async def get_ratings(client: redis.Redis, id: int):
    cache = RedisCachePickleCompressed(client)
    cache_key = f"athlete:ranking:{id}"
    return await cache.get(cache_key)
