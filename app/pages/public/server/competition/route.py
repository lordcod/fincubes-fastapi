
from datetime import date
from typing import List, Literal, Optional

from fastapi import APIRouter, Query
from tortoise.expressions import Q
from tortoise.functions import Count


from app.models.competition.competition import Competition
from app.models.competition.relay_result import RelayResult
from app.models.competition.result import Result
from app.schemas.competition.competition import CompetitionWithResults_Pydantic
from app.shared.utils.scopes.request import require_scope

router = APIRouter(tags=['Public/Server/Event'])


@router.get("/", response_model=List[CompetitionWithResults_Pydantic])
@require_scope('competition:read')
async def get_competitions(
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    query: Optional[str] = Query(default=None, min_length=1),
    status: Optional[str] = None,
    processed: Optional[bool] = None,
    has_results: Optional[bool] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    sort: Literal[
        "start_date",
        "-start_date",
        "end_date",
        "-end_date",
        "name",
        "-name",
        "last_processed_at",
        "-last_processed_at",
    ] = "-start_date",
):
    q_filter = Q()
    if query:
        q_filter &= (
            Q(name__icontains=query)
            | Q(location__icontains=query)
            | Q(city__icontains=query)
            | Q(organizer__icontains=query)
        )
    if status:
        q_filter &= Q(status=status)
    if processed is not None:
        q_filter &= Q(last_processed_at__isnull=not processed)
    if date_from is not None:
        q_filter &= Q(start_date__gte=date_from)
    if date_to is not None:
        q_filter &= Q(end_date__lte=date_to)

    base_query = Competition.filter(q_filter).order_by(sort)
    all_competitions = await base_query
    all_competition_ids = [competition.id for competition in all_competitions]
    results_count_by_competition = dict.fromkeys(all_competition_ids, 0)

    if all_competition_ids:
        result_counts = await Result.filter(
            competition_id__in=all_competition_ids
        ).annotate(results_count=Count("id")).group_by("competition_id").values(
            "competition_id",
            "results_count",
        )
        relay_result_counts = await RelayResult.filter(
            competition_id__in=all_competition_ids
        ).annotate(results_count=Count("id")).group_by("competition_id").values(
            "competition_id",
            "results_count",
        )

        for row in result_counts + relay_result_counts:
            competition_id = row["competition_id"]
            results_count_by_competition[competition_id] += row["results_count"]

    for competition in all_competitions:
        competition.results_count = results_count_by_competition[competition.id]
        competition.has_results = competition.results_count > 0

    if has_results is not None:
        all_competitions = [
            competition
            for competition in all_competitions
            if competition.has_results == has_results
        ]

    if offset is not None:
        all_competitions = all_competitions[offset:]
    if limit is not None:
        all_competitions = all_competitions[:limit]

    return all_competitions
