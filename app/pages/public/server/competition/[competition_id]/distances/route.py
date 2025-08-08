from fastapi import APIRouter, Depends
from tortoise.exceptions import DoesNotExist

from app.core.errors import APIError, ErrorCode

from app.models.competition.competition import Competition
from app.models.competition.distance import Distance
from app.schemas.competition.distance import (Distance_Pydantic,
                                              DistanceIn_Pydantic)
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.get("/", response_model=list[Distance_Pydantic])
@require_scope('competition.distances:read')
async def get_distances(competition_id: int):
    try:
        competition = await Competition.get(id=competition_id)

        distances = competition.distances.all().order_by("order")
        return await Distance_Pydantic.from_queryset(distances)
    except DoesNotExist:
        raise APIError(ErrorCode.COMPETITION_NOT_FOUND)
