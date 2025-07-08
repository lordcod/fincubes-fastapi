from fastapi import APIRouter, Depends
from tortoise.exceptions import DoesNotExist

from app.core.errors import APIError, ErrorCode
from app.core.security.deps.permissions import admin_required
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
