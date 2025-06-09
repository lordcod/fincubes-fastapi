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
    (r.result IS NOT NULL OR r.final IS NOT NULL) WHERE 
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


def get_current_season_year(current_date: date):
    if current_date.month >= 9:
        return current_date.year
    else:
        return current_date.year - 1


async def get_top_results(
    distance: int,
    stroke: str,
    gender: Optional[str] = None,
    limit: int = 3,
    offset: int = 0,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    competition_ids: Optional[Union[int, List[int]]] = None,
    season: Optional[int] = None,
    current_season: Optional[bool] = False
) -> List[Result]:
    if limit is None:
        limit = 3

    current_date = date.today()
    current_year = current_date.year

    if current_season:
        season = get_current_season_year(current_date)

    filters = Q(distance=distance, stroke=stroke)

    if season is not None:
        filters &= (Q(competition__start_date__gte=date(season, 9, 1)) &
                    Q(competition__end_date__lte=date(season + 1, 8, 31)))

    if gender is not None:
        filters &= Q(athlete__gender=gender)

    if min_age is not None:
        filters &= Q(athlete__birth_year__lte=current_year - min_age)
    if max_age is not None:
        filters &= Q(athlete__birth_year__gte=current_year - max_age)

    # Фильтр по соревнованиям
    if competition_ids:
        if isinstance(competition_ids, list):
            filters &= Q(competition_id__in=competition_ids)
        else:
            filters &= Q(competition_id=competition_ids)

    results_with_best = await Result.filter(filters).annotate(
        best=Case(
            When(
                Q(final__isnull=False) & (
                    Q(result__isnull=True) | Q(final__lt=F("result"))),
                then=F("final")
            ),
            default=F("result")
        )
    ).order_by("best").prefetch_related("athlete", "competition").all()

    seen = set()
    unique_results = []
    for res in results_with_best:
        if res.athlete_id not in seen:
            seen.add(res.athlete_id)
            unique_results.append(res)
        if offset:
            if limit and len(unique_results) >= limit+offset:
                break
        else:
            if limit and len(unique_results) >= limit:
                break

    return unique_results[offset:]
