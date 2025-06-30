from fastapi import APIRouter, Depends
from tortoise.exceptions import DoesNotExist

from app.core.errors import APIError, ErrorCode
from app.core.security.permissions import admin_required
from app.models.competition.distance import Distance
from app.schemas.competition.distance import (Distance_Pydantic,
                                              DistanceIn_Pydantic)

router = APIRouter()


@router.get("/", response_model=Distance_Pydantic)
async def get_distance(competition_id: int, distance_id: int):
    distance = await Distance.filter(
        id=distance_id, competition_id=competition_id
    ).first()
    if not distance:
        raise APIError(ErrorCode.DISTANCE_NOT_FOUND)
    return distance


@router.put(
    "/",
    dependencies=[Depends(admin_required)],
    response_model=Distance_Pydantic,
)
async def update_distance(
    competition_id: int, distance_id: int, distance: DistanceIn_Pydantic
):
    try:
        existing_distance = await Distance.filter(
            id=distance_id, competition_id=competition_id
        ).first()

        if not existing_distance:
            raise APIError(ErrorCode.DISTANCE_NOT_FOUND)

        existing_distance.stroke = distance.stroke
        existing_distance.distance = distance.distance
        existing_distance.category = distance.category
        existing_distance.order = distance.order
        existing_distance.gender = distance.gender

        await existing_distance.save()

        return existing_distance
    except DoesNotExist:
        raise APIError(ErrorCode.COMPETITION_NOT_FOUND)


@router.delete(
    "/",
    dependencies=[Depends(admin_required)],
    status_code=205,
)
async def delete_distance(competition_id: int, distance_id: int):
    distance = await Distance.filter(
        id=distance_id, competition_id=competition_id
    ).first()
    if distance:
        await distance.delete()
    else:
        raise APIError(ErrorCode.DISTANCE_NOT_FOUND)
