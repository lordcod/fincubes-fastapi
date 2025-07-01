from fastapi import APIRouter, Depends

from app.models.roles.coach import Coach
from app.schemas.users.coach import CoachIn, CoachOut
from app.shared.enums.enums import UserRoleEnum
from app.shared.utils.user_role import get_role

router = APIRouter(tags=['Me/Role/Coach'])


@router.put("/", response_model=CoachOut)
async def update_coach(
    updated: CoachIn, coach: Coach = Depends(get_role(UserRoleEnum.COACH))
):
    data = updated.model_dump()
    await coach.update_from_dict(data).save()
    return await CoachOut.from_tortoise_orm(coach)


@router.get("/", response_model=CoachOut)
async def get_coach_me(coach: Coach = Depends(get_role(UserRoleEnum.COACH))):
    return await CoachOut.from_tortoise_orm(coach)
