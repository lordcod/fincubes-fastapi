from fastapi import APIRouter, Depends
from tortoise.exceptions import DoesNotExist
from misc.errors import APIError, ErrorCode
from models.models import Athlete, User
from misc.security import admin_required


router = APIRouter()


@router.post("/athlete/{athlete_id}", dependencies=[Depends(admin_required)])
async def get_user_from_athlete_id(athlete_id: int):
    try:
        user = (
            await User.filter(athlete_id=athlete_id).prefetch_related("athlete").first()
        )
    except DoesNotExist:
        raise APIError(ErrorCode.USER_NOT_FOUND)
    return user


@router.post("/{user_id}/unassign-athlete", dependencies=[Depends(admin_required)])
async def unassign_athlete(user_id: int):
    user = await User.get_or_none(id=user_id)
    if not user:
        raise APIError(ErrorCode.USER_NOT_FOUND)
    user.athlete = None
    await user.save()
    return {"detail": "Athlete unassigned"}


@router.post(
    "/{user_id}/assign-athlete/{athlete_id}", dependencies=[Depends(admin_required)]
)
async def assign_athlete(user_id: int, athlete_id: int):
    try:
        user = await User.get(id=user_id)
    except DoesNotExist:
        raise APIError(ErrorCode.USER_NOT_FOUND)

    try:
        athlete = await Athlete.get(id=athlete_id)
    except DoesNotExist:
        raise APIError(ErrorCode.ATHLETE_NOT_FOUND)
    if user.athlete:
        raise APIError(ErrorCode.ATHLETE_ALREADY_BOUND_TO_OTHER_USER)

    user.athlete = athlete
    await user.save()


@router.post("/{user_id}/set-admin", dependencies=[Depends(admin_required)])
async def set_admin_status(user_id: int, value: bool):
    user = await User.get_or_none(id=user_id)
    if not user:
        raise APIError(ErrorCode.USER_NOT_FOUND)

    user.admin = value
    await user.save()
    return {"detail": f"Admin status set to {value}"}


@router.get("/search", dependencies=[Depends(admin_required)])
async def search_users(q: str):
    if q.isdigit():
        users = User.filter(id=int(q)).all()
    else:
        users = User.filter(email__icontains=q).all()
    users = await users.prefetch_related("athlete")
    return users
