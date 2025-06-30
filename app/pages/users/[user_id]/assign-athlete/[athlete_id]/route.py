from fastapi import APIRouter, Depends
from tortoise.exceptions import DoesNotExist

from app.core.errors import APIError, ErrorCode
from app.core.security.permissions import admin_required
from app.models.athlete.athlete import Athlete
from app.models.user.user import User

router = APIRouter()


@router.post(
    "/", dependencies=[Depends(admin_required)]
)
async def assign_athlete(user_id: int, athlete_id: int):
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
