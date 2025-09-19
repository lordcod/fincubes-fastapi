from typing import Optional
from fastapi import APIRouter
from app.models.user.user_role import UserRole
from app.schemas.users.role import UserRoleIn, UserRoleOut
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.get("/", response_model=Optional[UserRoleOut])
@require_scope('user:read')
async def get_user_role(id: int):
    user_role = await UserRole.filter(user_id=id).first()
    return user_role


@router.put("/", response_model=Optional[UserRoleOut])
@require_scope('user:write')
async def update_user_role(id: int, role: UserRoleIn):
    user_role = await UserRole.filter(user_id=id).first()
    if user_role is None:
        user_role = await UserRole.create(**role.model_dump())
    else:
        user_role.update_from_dict(role.model_dump())
        await user_role.save()
    return user_role


@router.delete("/", status_code=204)
@require_scope('user:delete')
async def delete_user_role(id: int):
    await UserRole.filter(user_id=id).delete()
