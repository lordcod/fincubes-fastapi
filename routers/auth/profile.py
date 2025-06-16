from typing import Optional

from fastapi import APIRouter, Depends

from misc.security import TokenType, UserAuthSecurity
from models.models import User, UserRole
from schemas.auth import UserResponse
from schemas.users.role import UserRoleOut

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def protected_endpoint(
    current_user: User = Depends(UserAuthSecurity(TokenType.access)),
):
    return current_user


@router.get("/me/role", response_model=Optional[UserRoleOut])
async def protected_role_endpoint(
    current_user: User = Depends(UserAuthSecurity(TokenType.access)),
):
    role = await UserRole.filter(user=current_user).first()
    if not role:
        return None

    return await UserRoleOut.from_tortoise_orm(role)
