from fastapi import APIRouter, Body, Depends

from app.core.errors import APIError, ErrorCode

from app.models.user.user import User
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.post("/", status_code=204)
@require_scope('*')
async def set_admin_status(id: int, value: bool = Body(embed=True)):
    user = await User.get_or_none(id=id)
    if not user:
        raise APIError(ErrorCode.USER_NOT_FOUND)

    scopes_set = set(user.scopes)
    if value:
        scopes_set.add('*')
    else:
        scopes_set.discard('*')
    user.scopes = list(scopes_set)

    await user.save()
