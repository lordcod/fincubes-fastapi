import zlib
import pickle
import hashlib
from redis.asyncio import Redis
from tortoise import Tortoise
from typing import Any, Optional
from datetime import date
from models.redis_client import client


sql = """
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
    WHERE r.stroke = $1
      AND r.distance = $2
      AND a.gender = $3
      AND (r.result IS NOT NULL OR r.final IS NOT NULL)
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
        r.athlete_id,
        r.stroke,
        r.distance,
        r.result AS result_result,
        r.final AS result_final,
        r.competition_id,

        a.first_name AS athlete_first_name,
        a.last_name AS athlete_last_name,
        a.gender AS athlete_gender,
        a.birth_year AS athlete_birth_year,

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
    {where}
)
SELECT *
FROM best_full_results
WHERE row_num > ${offset}
ORDER BY row_num
LIMIT ${limit};
"""


class RedisCachePickleCompressed:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def set(self, key: str, value: Any, expire_seconds: Optional[int] = None):
        data = pickle.dumps(value)
        compressed = zlib.compress(data)
        await self.redis.set(key, compressed, ex=expire_seconds)

    async def get(self, key: str) -> Optional[Any]:
        compressed = await self.redis.get(key)
        if compressed is None:
            return None
        data = zlib.decompress(compressed)
        return pickle.loads(data)


async def get_top_results(
    distance: int,
    stroke: str,
    gender: str,
    limit: int = 3,
    offset: int = 0,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    season: Optional[int] = None,
    current_season: Optional[bool] = False
):
    cache = RedisCachePickleCompressed(client)
    cache_key_raw = f"{stroke}:{distance}:{gender}:{limit}:{offset}:{min_age}:{max_age}:{season}:{current_season}"
    cache_key = "top_results:" + \
        hashlib.sha256(cache_key_raw.encode()).hexdigest()
    cached = await cache.get(cache_key)
    if cached:
        return cached

    current_date = date.today()
    current_year = current_date.year

    if current_season:
        if current_date.month >= 9:
            season = current_year
        else:
            season = current_year - 1

    if season is not None:
        season_start = date(season, 9, 1)
        season_end = date(season + 1, 8, 31)
    else:
        season_start = None
        season_end = None

    params = [
        stroke,
        distance,
        gender,
    ]
    conditions = []

    if min_age is not None:
        birth_max = current_year - min_age
        params.append(birth_max)
        conditions.append(f'CAST(a.birth_year AS INTEGER) <= ${len(params)}')

    if max_age is not None:
        birth_min = current_year - max_age
        params.append(birth_min)
        conditions.append(f'CAST(a.birth_year AS INTEGER) >= ${len(params)}')
    if season_start is not None and season_end is not None:
        params.append(season_start)
        conditions.append(f"c.start_date >= ${len(params)}")
        params.append(season_end)
        conditions.append(f"c.end_date <= ${len(params)}")

    if conditions:
        where = 'WHERE ' + ' AND '.join(conditions)
    else:
        where = ''

    params.append(offset)
    offset_num = len(params)
    params.append(limit)
    limit_num = len(params)

    sql_raw = sql.format(where=where,
                         offset=offset_num,
                         limit=limit_num)
    results = await Tortoise.get_connection("default").execute_query_dict(sql_raw, params)

    await cache.set(cache_key, results, expire_seconds=60*15)
    return results
