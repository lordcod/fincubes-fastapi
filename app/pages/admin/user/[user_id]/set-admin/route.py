from fastapi import APIRouter, Depends

from app.core.errors import APIError, ErrorCode
from app.core.security.deps.permissions import admin_required
from app.models.user.user import User

router = APIRouter()


@router.post("/", dependencies=[Depends(admin_required)])
async def set_admin_status(user_id: int, value: bool):
    user = await User.get_or_none(id=user_id)
    if not user:
        raise APIError(ErrorCode.USER_NOT_FOUND)

    user.admin = value
    await user.save()
    return {"detail": f"Admin status set to {value}"}
