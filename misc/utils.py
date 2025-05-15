from tortoise.expressions import Q, F, Case, When
from models.models import Result
from typing import Optional, List, Union
from datetime import date, time
import redis.asyncio as redis


lua_script = """
local zset_name = KEYS[1]
local score = ARGV[1]
local exists = redis.call('ZSCORE', zset_name, score)
if exists == false then
    redis.call('ZADD', zset_name, score, score)
end
return redis.call('ZRANK', zset_name, score)
"""


async def get_rank(
    client: redis.Redis,
    gender: str,
    stroke: str,
    distance: int,
    r_time: time
):
    time = (
        r_time.hour * 60 * 60
        + r_time.minute * 60
        + r_time.second
        + ((r_time.microsecond // 1000)/1000)
    )

    rank = await client.eval(lua_script, 1,
                             f"top:{gender}:{stroke}:{distance}",
                             time)
    return rank+1


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
            When(final__isnull=False, then=F("final")),
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
