import hashlib
from datetime import date
from typing import Optional

from tortoise import Tortoise

from app.shared.cache.redis_compressed import RedisCachePickleCompressed
from app.shared.clients.redis import client

BASE_SQL = """
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
    {where1}
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
        r.resolved_time AS result_resolved_time,

        r.athlete_id,
        a.first_name AS athlete_first_name,
        a.last_name AS athlete_last_name,
        a.gender AS athlete_gender,
        a.birth_year AS athlete_birth_year,
        a.club AS athlete_club,
        a.city AS athlete_city,

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
    {where2}
)
SELECT *
FROM best_full_results
{offset}
ORDER BY row_num
{limit}
"""


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

    current_date = date.today()
    current_year = current_date.year
    if current_season:
        season = current_year if current_date.month >= 9 else current_year - 1
    season_start = date(season, 9, 1) if season is not None else None
    season_end = date(season + 1, 8, 31) if season is not None else None

    params = []
    where1 = []
    where2 = []

    if stroke is not None:
        params.append(stroke)
        where1.append(f"AND r.stroke = ${len(params)}")

    if distance is not None:
        params.append(distance)
        where1.append(f"AND r.distance = ${len(params)}")

    if gender is not None:
        params.append(gender)
        where1.append(f"AND a.gender = ${len(params)}")

    if min_age is not None:
        birth_max = current_year - min_age
        params.append(birth_max)
        where2.append(f"CAST(a.birth_year AS INTEGER) <= ${len(params)}")

    if max_age is not None:
        birth_min = current_year - max_age
        params.append(birth_min)
        where2.append(f"CAST(a.birth_year AS INTEGER) >= ${len(params)}")

    if season_start and season_end:
        params.append(season_start)
        where2.append(f"c.start_date >= ${len(params)}")
        params.append(season_end)
        where2.append(f"c.end_date <= ${len(params)}")

    if offset is not None:
        params.append(offset)
        offset = f"WHERE row_num > ${len(params)}"
    else:
        offset = ''

    if limit is not None:
        params.append(limit)
        limit = f'LIMIT ${len(params)};'
    else:
        limit = ''

    sql_final = BASE_SQL.format(
        where1=" " + " ".join(where1) if where1 else "",
        where2="WHERE " + " AND ".join(where2) if where2 else "",
        offset=offset,
        limit=limit
    )

    results = await Tortoise.get_connection(
        "default").execute_query_dict(
            sql_final, params)
    await cache.set(cache_key, results, expire_seconds=60 * 60)
    return results
