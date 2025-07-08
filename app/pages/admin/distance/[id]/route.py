from fastapi import APIRouter, Depends
from tortoise.exceptions import DoesNotExist

from app.core.errors import APIError, ErrorCode
from app.core.security.deps.permissions import admin_required
from app.models.competition.distance import Distance
from app.schemas.competition.distance import (Distance_Pydantic,
                                              DistanceIn_Pydantic)

router = APIRouter()


@router.put(
    "/",
    dependencies=[Depends(admin_required)],
    response_model=Distance_Pydantic,
)
async def update_distance(
    id: int,
    distance: DistanceIn_Pydantic
):
    try:
        existing_distance = await Distance.get(
            id=id
        )
        if not existing_distance:
            raise APIError(ErrorCode.DISTANCE_NOT_FOUND)

        existing_distance = await existing_distance.update_from_dict(distance.model_dump())
        return existing_distance
    except DoesNotExist:
        raise APIError(ErrorCode.COMPETITION_NOT_FOUND)


@router.delete(
    "/",
    dependencies=[Depends(admin_required)],
    status_code=205,
)
async def delete_distance(id: int):
    distance = await Distance.get(id=id)
    if distance:
        await distance.delete()
    raise APIError(ErrorCode.DISTANCE_NOT_FOUND)
