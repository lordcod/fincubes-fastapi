
from typing import List, Optional

from fastapi import APIRouter
from tortoise.functions import Count


from app.models.competition.competition import Competition
from app.models.competition.relay_result import RelayResult
from app.models.competition.result import Result
from app.schemas.competition.competition import CompetitionWithResults_Pydantic
from app.shared.utils.scopes.request import require_scope

router = APIRouter(tags=['Public/Server/Event'])


@router.get("/", response_model=List[CompetitionWithResults_Pydantic])
@require_scope('competition:read')
async def get_competitions(limit: Optional[int] = None, offset: Optional[int] = None):
    query = Competition.all().order_by("-start_date")

    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)

    competitions = await query
    competition_ids = [competition.id for competition in competitions]

    if not competition_ids:
        return competitions

    result_counts = await Result.filter(
        competition_id__in=competition_ids
    ).annotate(results_count=Count("id")).group_by("competition_id").values(
        "competition_id",
        "results_count",
    )
    relay_result_counts = await RelayResult.filter(
        competition_id__in=competition_ids
    ).annotate(results_count=Count("id")).group_by("competition_id").values(
        "competition_id",
        "results_count",
    )

    results_count_by_competition = dict.fromkeys(competition_ids, 0)
    for row in result_counts + relay_result_counts:
        competition_id = row["competition_id"]
        results_count_by_competition[competition_id] += row["results_count"]

    for competition in competitions:
        competition.results_count = results_count_by_competition[competition.id]
        competition.has_results = competition.results_count > 0

    return competitions
