import asyncio
from typing import Dict, List, Tuple

from fastapi import APIRouter, Depends
from tortoise.exceptions import DoesNotExist

from app.core.deps.redis import get_redis
from app.core.errors import APIError, ErrorCode
from app.models.athlete.athlete import Athlete
from app.models.competition.result import CompetitionResult, CompetitionStage
from app.schemas.athlete.performance import (
    ResultDepth0_Pydantic,
    UserAthleteResults,
    UserCompetitionResult,
    UserPerformance
)
from app.shared.cache.redis_compressed import RedisCachePickleCompressed
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.get("/", response_model=UserAthleteResults)
@require_scope("athlete.results:read")
async def get_athlete_results(id: int, redis=Depends(get_redis)):
    cache_key = f"performances:{id}"
    cache = RedisCachePickleCompressed(redis)

    # Проверка кэша
    cached = await cache.get(cache_key)
    if cached:
        return cached

    try:
        athlete = await Athlete.get(id=id)
    except DoesNotExist:
        raise APIError(ErrorCode.ATHLETE_NOT_FOUND)

    results_query = await CompetitionResult.filter(
        athlete_id=id
    ).prefetch_related("competition", "stages")

    competitions: Dict[int, Dict] = {}
    best_results: Dict[Tuple[str, int], UserPerformance] = {}

    for result in results_query:
        competition_id = result.competition.id
        if competition_id not in competitions:
            competitions[competition_id] = {
                "competition": result.competition,
                "performances": [],
            }

        resolved_time = result.resolved_time
        performance_data = await ResultDepth0_Pydantic.from_tortoise_orm(result)
        performances = UserPerformance(
            **performance_data.model_dump(), best=False)

        key = (result.stroke, result.distance)
        best_performance = best_results.get(key)

        is_new_best = resolved_time and (
            best_performance is None or best_performance.resolved_time > resolved_time
        )
        if is_new_best:
            if best_performance:
                best_performance.best = False
            performances.best = True
            best_results[key] = performances

        competitions[competition_id]["performances"].append(performances)

    competitions_sorted = dict(
        sorted(
            competitions.items(),
            key=lambda item: item[1]["competition"].start_date,
            reverse=True
        )
    )

    competition_results = [
        UserCompetitionResult(**comp) for comp in competitions_sorted.values()
    ]

    model = UserAthleteResults(
        id=athlete.id,
        results=competition_results
    ).model_dump()

    await cache.set(cache_key, model, expire_seconds=60 * 15)
    return model
