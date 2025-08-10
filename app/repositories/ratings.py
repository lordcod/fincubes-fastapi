import logging
from collections import defaultdict
from datetime import time

import redis.asyncio as redis

from app.repositories.get_top_results import get_top_results
from app.schemas.results.top import parse_best_full_result
from app.shared.cache.redis_compressed import RedisCachePickleCompressed
from app.shared.utils.metadata import categories

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
    _log.info("Starting athlete rankings update")

    athlete_results = defaultdict(lambda: defaultdict(list))

    for season in [True, False]:
        season_str = 'current_season' if season else 'global'
        for category in categories:
            _log.debug("Processing category '%s' for season '%s'",
                       category['name'], season_str)

            results = await get_top_results(min_age=category['min_age'],
                                            max_age=category['max_age'],
                                            current_season=season)
            results = [parse_best_full_result(res) for res in results]
            for top in results:
                athlete_results[top.athlete.id][season_str + ':' + category['id']
                                                ].append(top.model_dump())
    _log.info("Collected results for %d athletes", len(athlete_results))

    pipe = client.pipeline()
    cache = RedisCachePickleCompressed(pipe)
    for athlete_id, results in athlete_results.items():
        cache_key = f"athlete:ranking:{athlete_id}"
        await cache.set(cache_key, dict(results))
    await pipe.execute()
    _log.info("Saved ranking results for athletes")


async def get_ratings(client: redis.Redis, id: int):
    cache = RedisCachePickleCompressed(client)
    cache_key = f"athlete:ranking:{id}"
    return await cache.get(cache_key)
