
from typing import Optional

from fastapi import APIRouter, Depends

from app.core.security.auth import UserAuthSecurity
from app.core.security.schema import TokenType
from app.models.user.user import User
from app.models.user.user_role import UserRole
from app.schemas.users.role import UserRoleOut

router = APIRouter()


@router.get("/", response_model=Optional[UserRoleOut])
async def protected_role_endpoint(
    current_user: User = Depends(UserAuthSecurity(TokenType.access)),
):
    role = await UserRole.filter(user=current_user).first()
    if not role:
        return None

    return await UserRoleOut.from_tortoise_orm(role)
