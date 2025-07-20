from fastapi import APIRouter, Body, Depends
from tortoise.exceptions import DoesNotExist

from app.core.errors import APIError, ErrorCode
from app.core.security.deps.permissions import admin_required
from app.models.athlete.athlete import Athlete
from app.models.user.user import User

router = APIRouter()


@router.post(
    "/", dependencies=[Depends(admin_required)]
)
async def assign_athlete(user_id: int, athlete_id: int = Body(embed=True)):
    try:
        user = await User.get(id=user_id)
    except DoesNotExist as exc:
        raise APIError(ErrorCode.USER_NOT_FOUND) from exc

    try:
        athlete = await Athlete.get(id=athlete_id)
    except DoesNotExist as exc:
        raise APIError(ErrorCode.ATHLETE_NOT_FOUND) from exc
    if user.athlete:
        raise APIError(ErrorCode.ATHLETE_ALREADY_BOUND_TO_OTHER_USER)

    user.athlete = athlete
    await user.save()


@router.delete("/", dependencies=[Depends(admin_required)])
async def unassign_athlete(user_id: int):
    user = await User.get_or_none(id=user_id)
    if not user:
        raise APIError(ErrorCode.USER_NOT_FOUND)
    user.athlete = None
    await user.save()
    return {"detail": "Athlete unassigned"}
