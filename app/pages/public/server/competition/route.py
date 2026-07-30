
from typing import List, Optional

from fastapi import APIRouter


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

    result_competition_ids = await Result.filter(
        competition_id__in=competition_ids
    ).distinct().values_list("competition_id", flat=True)
    relay_result_competition_ids = await RelayResult.filter(
        competition_id__in=competition_ids
    ).distinct().values_list("competition_id", flat=True)
    competitions_with_results = (
        set(result_competition_ids) | set(relay_result_competition_ids)
    )

    for competition in competitions:
        competition.has_results = competition.id in competitions_with_results

    return competitions
