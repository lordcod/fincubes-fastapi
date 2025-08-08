from fastapi import APIRouter, Depends
from tortoise.exceptions import DoesNotExist

from app.core.errors import APIError, ErrorCode

from app.models.competition.distance import Distance
from app.schemas.competition.distance import (Distance_Pydantic,
                                              DistanceIn_Pydantic)
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.put(
    "/",
    response_model=Distance_Pydantic,
)
@require_scope('distance:write')
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
    status_code=205,
)
@require_scope('distance:delete')
async def delete_distance(id: int):
    distance = await Distance.get(id=id)
    if distance:
        await distance.delete()
    raise APIError(ErrorCode.DISTANCE_NOT_FOUND)
