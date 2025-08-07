
from typing import List

from fastapi import APIRouter, Body, Depends
from tortoise.exceptions import DoesNotExist

from app.core.errors import APIError, ErrorCode

from app.models.competition.distance import Distance
from app.schemas.competition.distance import (Distance_Pydantic,
                                              DistanceOrderUpdate_Pydantic)
from app.shared.clients.scopes.request import require_scope

router = APIRouter()


@router.put(
    "/",
    response_model=List[Distance_Pydantic],
)
@require_scope('distance:write')
async def bulk_update_distances(
    distances: List[DistanceOrderUpdate_Pydantic],
    competition_id: int = Body(embed=True),
):
    try:
        existing_distances = await Distance.filter(
            id__in=[d.id for d in distances], competition_id=competition_id
        ).all()
        if len(existing_distances) != len(distances):
            raise APIError(ErrorCode.DISTANCE_NOT_FOUND)

        dists = {}
        for dist in existing_distances:
            dists[dist.id] = dist

        new = []
        for update in distances:
            dist = dists[update.id]
            dist.order = update.order
            new.append(dist)
        await Distance.bulk_update(new, ["order"])

        return new
    except DoesNotExist as exc:
        raise APIError(ErrorCode.COMPETITION_NOT_FOUND) from exc
