import logging
from tortoise import Tortoise
from tortoise.expressions import Q, F, Case, When
from models.models import Result
from typing import Optional, List, Union
from datetime import date, time
import redis.asyncio as redis


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
SELECT
    r.athlete_id,
    r.id,
    r.stroke,
    r.distance,
    a.gender,
    MIN(CASE
        WHEN r.final IS NOT NULL AND (r.result IS NULL OR r.final < r.result)
        THEN r.final
        ELSE r.result
    END) AS best_result
FROM
    results r
JOIN
    athletes a ON a.id = r.athlete_id
WHERE
    (r.result IS NOT NULL OR r.final IS NOT NULL) AND r.stroke = 'BIFINS'
      AND r.distance = '100'
      AND a.gender = 'F' 
GROUP BY
    r.athlete_id, r.stroke, r.distance, a.gender;"""


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
        .execute_query(ranking_sql_raw)
    )
    return results


async def update_ratings(client: redis.Redis):
    _log.debug("Start updateing rating")

    total = await Result.all().count()
    _log.debug(f"Total results: {total}")

    results = await get_best_results_raw()
    rating_data = {}
    for (athlete_id, stroke, distance, gender, best_result_seconds) in results:
        key = f"ranking:{gender}:{stroke}:{distance}"
        score = as_duration(best_result_seconds)

        if key not in rating_data:
            rating_data[key] = {}
        rating_data[key][athlete_id] = score

    pipe = client.pipeline()
    for key, members in rating_data.items():
        pipe.delete(key+':results')
        pipe.delete(key+':times')
        pipe.zadd(key+':results', members)
        pipe.zadd(key+':times', {str(score): score for score in members.values()})
    await pipe.execute()
