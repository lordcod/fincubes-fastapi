from fastapi import APIRouter, Body, Depends
from tortoise.exceptions import DoesNotExist

from app.core.errors import APIError, ErrorCode
from app.core.security.permissions import admin_required
from app.models.competition.competition import Competition
from app.models.competition.distance import Distance
from app.schemas.competition.distance import (Distance_Pydantic,
                                              DistanceIn_Pydantic)

router = APIRouter(tags=['Admin/Distance'])


@router.post(
    "/", dependencies=[Depends(admin_required)], response_model=Distance_Pydantic
)
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
