from fastapi import APIRouter, Depends
from tortoise.exceptions import DoesNotExist

from app.core.errors import APIError, ErrorCode
from app.core.security.permissions import admin_required
from app.models.competition.competition import Competition
from app.models.competition.distance import Distance
from app.schemas.competition.distance import (Distance_Pydantic,
                                              DistanceIn_Pydantic)

router = APIRouter()


@router.get("/", response_model=list[Distance_Pydantic])
async def get_distances(competition_id: int):
    try:
        competition = await Competition.get(id=competition_id)

        distances = competition.distances.all().order_by("order")
        return await Distance_Pydantic.from_queryset(distances)
    except DoesNotExist:
        raise APIError(ErrorCode.COMPETITION_NOT_FOUND)


@router.post(
    "/", dependencies=[Depends(admin_required)], response_model=Distance_Pydantic
)
async def create_distance(competition_id: int, distance: DistanceIn_Pydantic):
    try:
        kwargs = distance.dict()
        competition = await Competition.get(id=competition_id)
        new_distance = await Distance.create(**kwargs, competition=competition)
        return new_distance
    except DoesNotExist:
        raise APIError(ErrorCode.COMPETITION_NOT_FOUND)
