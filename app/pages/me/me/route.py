from fastapi import APIRouter, Depends

from app.core.security.deps.user_auth import UserAuthSecurity
from app.core.security.schema import TokenType
from app.models.user.user import User
from app.schemas.auth.auth import UserResponse

router = APIRouter(tags=['Me/Me'])


@router.get("/", response_model=UserResponse)
async def protected_endpoint(
    current_user: User = Depends(UserAuthSecurity()),
):
    return current_user
