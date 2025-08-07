from re import A
from typing import List, Optional
from fastapi import APIRouter
from app.core.errors import APIError, ErrorCode
from app.models.user.user import User
from app.schemas.auth.auth import UserResponse
from app.shared.clients.scopes.request import require_scope

router = APIRouter()


@router.get("/",  response_model=List[UserResponse])
@require_scope('user:read')
async def get_user(
    id: Optional[int] = None,
    email: Optional[str] = None,
):
    if id is not None and email is not None:
        raise APIError(ErrorCode.UNPROCESSABLE_ENTITY)
    if id is not None:
        return await User.filter(id=id)
    if email is not None:
        return await User.filter(email=email)
    return await User.all()
