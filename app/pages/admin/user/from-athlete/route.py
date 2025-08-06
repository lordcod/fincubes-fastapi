
from fastapi import APIRouter, Body, Depends
from tortoise.exceptions import DoesNotExist

from app.core.errors import APIError, ErrorCode

from app.models.user.user import User
from app.schemas.auth.auth import UserResponse
from app.shared.clients.scopes.request import require_scope

router = APIRouter()


@router.post("/", response_model=UserResponse)
@require_scope('user.athlete:read')
async def get_user_from_athlete_id(athlete_id: int = Body(embed=True)):
    try:
        user = (
            await User.filter(athlete_id=athlete_id).prefetch_related("athlete").first()
        )
    except DoesNotExist:
        raise APIError(ErrorCode.USER_NOT_FOUND)
    return user
