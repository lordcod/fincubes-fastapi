from fastapi import APIRouter, Depends

from app.core.errors import APIError, ErrorCode

from app.models.user.user import User
from app.schemas.auth.auth import UserResponse
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.get("/", response_model=UserResponse)
@require_scope('user:read')
async def get_user(id: int):
    user = await User.get_or_none(id=id)
    if not user:
        raise APIError(ErrorCode.USER_NOT_FOUND)
    return user
