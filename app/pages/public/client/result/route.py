from typing import List, Optional
from fastapi import APIRouter

from app.models.competition.result import CompetitionResult
from app.schemas.results.result import Result_Pydantic
from app.shared.utils.scopes.request import require_scope

router = APIRouter(tags=["Public/Client/Results"])


@router.get("/", response_model=List[Result_Pydantic])
@require_scope("client.result:read")
async def get_results(
    competition_id: Optional[int] = None,
    stroke: Optional[str] = None,
    distance: Optional[int] = None,
    gender: Optional[str] = None,
):
    filters = {}

    if competition_id is not None:
        filters["competition_id"] = competition_id
    if stroke is not None:
        filters["stroke"] = stroke
    if distance is not None:
        filters["distance"] = distance
    if gender is not None:
        filters["athlete__gender"] = gender

    query = CompetitionResult.filter(**filters)
    return await Result_Pydantic.from_queryset(query)
