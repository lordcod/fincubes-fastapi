from collections import defaultdict
import json
import logging
from tortoise import Tortoise
from datetime import time
import redis.asyncio as redis

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
ranking_sql_raw = """
WITH results_with_effective AS (
    SELECT
        r.*,
        a.gender,
        CASE
            WHEN r.final IS NOT NULL AND (r.result IS NULL OR r.final < r.result)
            THEN r.final
            ELSE r.result
        END AS effective_result
    FROM results r
    JOIN athletes a ON a.id = r.athlete_id
    WHERE (r.result IS NOT NULL OR r.final IS NOT NULL)
),
best_results AS (
    SELECT
        athlete_id,
        stroke,
        distance,
        gender,
        MIN(effective_result) AS best_result
    FROM results_with_effective
    GROUP BY athlete_id, stroke, distance, gender
),
best_full_results AS (
    SELECT
        r.id AS result_id,
        r.stroke,
        r.distance,
        r.result AS result_result,
        r.final AS result_final,

        r.athlete_id,
        a.first_name AS athlete_first_name,
        a.last_name AS athlete_last_name,
        a.gender AS athlete_gender,
        a.birth_year AS athlete_birth_year,

        r.competition_id,
        c.name AS competition_name,
        c.date AS competition_date,
        c.start_date AS competition_start_date,
        c.end_date AS competition_end_date,

        r.effective_result AS best,

        DENSE_RANK() OVER (
            PARTITION BY r.stroke, r.distance, a.gender
            ORDER BY r.effective_result
        ) AS row_num
    FROM results_with_effective r
    JOIN athletes a ON a.id = r.athlete_id
    JOIN competitions c ON c.id = r.competition_id
    JOIN best_results br
      ON r.athlete_id = br.athlete_id
     AND r.stroke = br.stroke
     AND r.distance = br.distance
     AND r.effective_result = br.best_result
)
SELECT *
FROM best_full_results
ORDER BY row_num;
"""


def as_duration(result: time):
    return (
        result.hour * 60 * 60
        + result.minute * 60
        + result.second
        + ((result.microsecond // 1000)/1000)
    )


async def get_rank(
    client: redis.Redis,
    gender: str,
    stroke: str,
    distance: int,
    result_time: time
):
    result = as_duration(result_time)

    rank = await client.eval(lua_script, 1,
                             f"top:{gender}:{stroke}:{distance}",
                             result)
    return rank+1


async def get_best_results_raw():
    results = (
        await Tortoise
        .get_connection("default")
        .execute_query_dict(ranking_sql_raw)
    )
    return [parse_best_full_result(res) for res in results]


async def update_ratings(client: redis.Redis):
    _log.debug("Start updating athlete rankings")

    results = await get_best_results_raw()
    athlete_results = defaultdict(dict)

    for top in results:
        key = f"{top.athlete.gender}:{top.result.stroke}:{top.result.distance}"
        athlete_results[top.athlete.id][key] = top.model_dump()

    pipe = client.pipeline()
    cache = RedisCachePickleCompressed(pipe)
    for athlete_id, results in athlete_results.items():
        cache_key = f"athlete:ranking:{athlete_id}"
        await cache.set(cache_key, results)
    await pipe.execute()


async def get_ratings(client: redis.Redis, id: int):
    cache = RedisCachePickleCompressed(client)
    cache_key = f"athlete:ranking:{id}"
    return await cache.get(cache_key)
