from fastapi import APIRouter, Body, Depends
from tortoise.exceptions import DoesNotExist

from app.core.errors import APIError, ErrorCode

from app.models.competition.competition import Competition
from app.models.competition.distance import Distance
from app.schemas.competition.distance import (Distance_Pydantic,
                                              DistanceIn_Pydantic)
from app.shared.clients.scopes.request import require_scope

router = APIRouter(tags=['Admin/Distance'])


@router.post(
    "/",
    response_model=Distance_Pydantic
)
@require_scope('distance:create')
async def create_distance(
    distance: DistanceIn_Pydantic,
    competition_id: int = Body(embed=True),
):
    try:
        kwargs = distance.dict()
        competition = await Competition.get(id=competition_id)
        new_distance = await Distance.create(**kwargs, competition=competition)
        return new_distance
    except DoesNotExist:
        raise APIError(ErrorCode.COMPETITION_NOT_FOUND)
