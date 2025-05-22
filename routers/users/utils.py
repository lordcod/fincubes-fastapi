from tkinter.tix import Tree
from typing import List, Optional
from fastapi import APIRouter, Body, HTTPException, Depends
from tortoise.exceptions import DoesNotExist
from misc.errors import APIError, ErrorCode
from models.models import Athlete, Parent, User, UserRole, Coach
from models.enums import UserRoleEnum
from misc.security import get_current_user
from schemas.athlete import Athlete_Pydantic


model_map = {
    UserRoleEnum.ATHLETE: Athlete,
    UserRoleEnum.COACH: Coach,
    UserRoleEnum.PARENT: Parent
}


async def get_profile(user: User, expected_role: UserRoleEnum):
    role = await UserRole.filter(user=user).first()
    if not role or role.role_type != expected_role:
        raise APIError(ErrorCode.INVALID_ROLE)

    model = model_map[role.role_type]
    return await model.get(id=role.profile_id)


def get_role(expected_role: UserRoleEnum):
    async def wrapped(user: User = Depends(get_current_user)):
        return await get_profile(user, expected_role)
    return wrapped
