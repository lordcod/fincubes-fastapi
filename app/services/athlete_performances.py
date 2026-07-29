from typing import Dict, Tuple

from app.core.errors import APIError, ErrorCode
from app.models.athlete.athlete import Athlete
from app.models.competition.relay_leg import RelayLeg
from app.models.competition.result import Result
from app.schemas.athlete.performance import (
    UserAthleteResults,
    UserCompetitionResult,
    UserPerformance,
)
from app.schemas.results.result import ResultDepth0_Pydantic
from app.shared.enums.enums import EventTypeEnum


def athlete_performances_cache_key(athlete_id: int) -> str:
    return f"performances:v2:{athlete_id}"


async def build_athlete_performances(
    athlete_id: int,
) -> UserAthleteResults:
    athlete = await Athlete.get_or_none(id=athlete_id)
    if athlete is None:
        raise APIError(ErrorCode.ATHLETE_NOT_FOUND)

    individual_results = await Result.filter(
        athlete_id=athlete_id,
    ).prefetch_related("competition")
    relay_legs = await RelayLeg.filter(
        athlete_id=athlete_id,
    ).prefetch_related("relay_result__competition")

    competitions = {}
    best_results: Dict[Tuple[str, int], UserPerformance] = {}

    for result in individual_results:
        competition = result.competition
        competition_id = competition.id
        if competition_id not in competitions:
            competitions[competition_id] = {
                "competition": competition,
                "performances": [],
            }

        result_data = await ResultDepth0_Pydantic.from_tortoise_orm(result)
        performance = UserPerformance(
            **result_data.model_dump(),
            relay_count=1,
            total_distance=result.distance,
        )

        key = (result.stroke, result.distance)
        best_performance = best_results.get(key)

        is_new_best = result.resolved_time and (
            best_performance is None
            or best_performance.resolved_time > result.resolved_time
        )
        if is_new_best:
            if best_performance:
                best_performance.best = False
            performance.best = True
            best_results[key] = performance

        competitions[competition_id]["performances"].append(performance)

    for leg in relay_legs:
        relay_result = leg.relay_result
        competition = relay_result.competition
        competition_id = competition.id
        if competition_id not in competitions:
            competitions[competition_id] = {
                "competition": competition,
                "performances": [],
            }

        performance = UserPerformance(
            id=relay_result.id,
            created_at=relay_result.created_at,
            updated_at=relay_result.updated_at,
            event_type=EventTypeEnum.RELAY,
            stroke=relay_result.stroke,
            distance=relay_result.distance,
            relay_count=relay_result.relay_count,
            total_distance=relay_result.total_distance,
            name=relay_result.name,
            result=relay_result.result,
            split_result=leg.result,
            relay_order=leg.order,
            relay_leg_id=leg.id,
            final=None,
            resolved_time=relay_result.result,
            place=relay_result.place,
            final_rank=None,
            points=relay_result.points,
            record=None,
            status=relay_result.status,
            metadata=relay_result.metadata,
            leg_metadata=leg.metadata,
            best=False,
        )
        competitions[competition_id]["performances"].append(performance)

    sorted_competitions = sorted(
        competitions.values(),
        key=lambda item: item["competition"].start_date,
        reverse=True,
    )
    return UserAthleteResults(
        id=athlete.id,
        results=[
            UserCompetitionResult(**competition)
            for competition in sorted_competitions
        ],
    )
