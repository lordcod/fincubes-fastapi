
import asyncio
from datetime import time
from typing import List, Tuple

from fastapi import APIRouter, Depends
from tortoise.exceptions import DoesNotExist

from app.core.deps.redis import get_redis
from app.core.errors import APIError, ErrorCode
from app.core.protection.secure_request import SecureRequest
from app.models.athlete.athlete import Athlete
from app.models.competition.result import Result
from app.repositories.ratings import get_rank
from app.schemas.athlete.performance import (UserAthleteResults,
                                             UserCompetitionResult)
from app.shared.cache.redis_compressed import RedisCachePickleCompressed

router = APIRouter()


@router.get("/", response_model=UserAthleteResults, dependencies=[Depends(SecureRequest(['athlete.results:read']))])
async def get_athlete_results(id: int, redis=Depends(get_redis)):
    cache_key = f"performances:{id}"
    cache = RedisCachePickleCompressed(redis)
    cached = await cache.get(cache_key)
    if cached:
        return cached

    try:
        athlete = await Athlete.get(id=id)
        results_query = await Result.filter(athlete=athlete).prefetch_related(
            "competition"
        )
    except DoesNotExist:
        raise APIError(ErrorCode.ATHLETE_NOT_FOUND)

    competitions = {}
    best_results = {}
    sem = asyncio.Semaphore(20)

    async def get_rank_safe(gender, stroke, distance, min_time):
        if min_time is None:
            return None
        async with sem:
            rank = await get_rank(redis, gender, stroke, distance, min_time)
            return rank

    rank_calls: List[Tuple[Result, time]] = []
    for result in results_query:
        min_time = (
            result.final
            if result.final and result.final <= result.result
            else result.result
        )
        rank_calls.append((result, min_time))

    tasks = [
        get_rank_safe(athlete.gender, result.stroke, result.distance, min_time)
        for result, min_time in rank_calls
    ]
    ranks = await asyncio.gather(*tasks)

    for (result, min_time), top_rank in zip(rank_calls, ranks):
        competition_id = result.competition.id
        if competition_id not in competitions:
            competitions[competition_id] = {
                "id": result.competition.id,
                "date": result.competition.date,
                "start_date": result.competition.start_date,
                "competition": result.competition.name,
                "performances": [],
            }

        performances = {
            "stroke": result.stroke,
            "distance": result.distance,
            "result": result.result,
            "final": result.final,
            "place": result.place,
            "final_rank": result.final_rank,
            "points": result.points,
            "record": result.record,
            "dsq": result.dsq,
            "dsq_final": result.dsq_final,
            "min_time": min_time,
            "top_rank": top_rank,
        }

        key = (result.stroke, result.distance)
        best_performance = best_results.get(key)
        if min_time and (
            best_performance is None or (
                best_performance["min_time"] > min_time)
        ):
            if best_performance:
                best_performance.pop("best", None)
            performances["best"] = True
            best_results[key] = performances

        competitions[competition_id]["performances"].append(performances)

    competitions = dict(
        sorted(
            competitions.items(), key=lambda item: item[1]["start_date"], reverse=True
        )
    )
    competition_results = [
        UserCompetitionResult(**comp) for comp in competitions.values()
    ]
    model = UserAthleteResults(
        id=athlete.id, results=competition_results
    ).model_dump()
    await cache.set(cache_key, model, expire_seconds=60 * 15)
    return model
