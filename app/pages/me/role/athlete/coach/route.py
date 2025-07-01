from typing import List

from fastapi import APIRouter, Body, Depends

from app.core.errors import APIError, ErrorCode
from app.models.athlete.athlete import Athlete
from app.models.roles.coach import Coach
from app.models.roles.coach_athlete import CoachAthlete
from app.schemas.users.coach import CoachOut, CoachOutWithStatus
from app.shared.enums.enums import UserRoleEnum
from app.shared.utils.user_role import get_role

router = APIRouter()


@router.get("/", response_model=List[CoachOutWithStatus])
async def get_coach(athlete: Athlete = Depends(get_role(UserRoleEnum.ATHLETE))):
    linked = await CoachAthlete.filter(athlete=athlete).select_related("coach")

    return [
        {**(await CoachOut.from_tortoise_orm(link.coach)).model_dump(), "status": link.status}
        for link in linked
    ]


@router.post("/")
async def add_coach(
    coach_id: int = Body(embed=True),
    athlete: Athlete = Depends(get_role(UserRoleEnum.ATHLETE)),
):
    coach = await Coach.get(id=coach_id)
    link = await CoachAthlete.filter(coach=coach, athlete=athlete).first()

    if not link or link.status in ("pending", "rejected_athlete"):
        status = "accepted"
    else:
        return {"success": False, "status": link.status}
    if link:
        link.status = status
        await link.save()
    else:
        await CoachAthlete.create(coach=coach, athlete=athlete, status=status)
    return {"success": True, "status": status}


@router.delete("/", status_code=204)
async def reject_coach(
    coach_id: int = Body(embed=True),
    athlete: Athlete = Depends(get_role(UserRoleEnum.ATHLETE)),
):
    coach = await Coach.get(id=coach_id)
    link = await CoachAthlete.filter(coach=coach, athlete=athlete).first()
    if not link:
        raise APIError(ErrorCode.ATHLETE_COACH_NOT_FOUND)

    link.status = "rejected_athlete"
    await link.save()
