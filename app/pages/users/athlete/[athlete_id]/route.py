
from fastapi import APIRouter, Depends
from tortoise.exceptions import DoesNotExist

from app.core.errors import APIError, ErrorCode
from app.core.security.permissions import admin_required
from app.models.user.user import User

router = APIRouter()


@router.post("/", dependencies=[Depends(admin_required)])
async def get_user_from_athlete_id(athlete_id: int):
    try:
        user = (
            await User.filter(athlete_id=athlete_id).prefetch_related("athlete").first()
        )
    except DoesNotExist:
        raise APIError(ErrorCode.USER_NOT_FOUND)
    return user
