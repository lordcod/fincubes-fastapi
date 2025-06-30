from fastapi import APIRouter, Depends

from app.core.errors import APIError, ErrorCode
from app.core.security.permissions import admin_required
from app.models.user.user import User

router = APIRouter()


@router.post("/", dependencies=[Depends(admin_required)])
async def unassign_athlete(user_id: int):
    user = await User.get_or_none(id=user_id)
    if not user:
        raise APIError(ErrorCode.USER_NOT_FOUND)
    user.athlete = None
    await user.save()
    return {"detail": "Athlete unassigned"}
