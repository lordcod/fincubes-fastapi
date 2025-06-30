from fastapi import APIRouter, Depends

from app.core.security.auth import UserAuthSecurity
from app.core.security.schema import TokenType
from app.models.user.user import User
from app.schemas.auth.auth import UserResponse

router = APIRouter()


@router.get("/", response_model=UserResponse)
async def protected_endpoint(
    current_user: User = Depends(UserAuthSecurity(TokenType.access)),
):
    return current_user
