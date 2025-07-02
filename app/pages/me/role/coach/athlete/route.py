

from typing import List

from fastapi import APIRouter, Body, Depends

from app.core.errors import APIError, ErrorCode
from app.models.athlete.athlete import Athlete
from app.models.roles.coach import Coach
from app.models.roles.coach_athlete import CoachAthlete
from app.schemas.athlete.athlete import Athlete_Pydantic
from app.shared.enums.enums import UserRoleEnum
from app.shared.utils.user_role import get_role

router = APIRouter()


@router.get("/", response_model=List[Athlete_Pydantic])
async def get_athletes(coach: Coach = Depends(get_role(UserRoleEnum.COACH))):
    linked = await CoachAthlete.filter(coach=coach).select_related("athlete")
    return [await Athlete_Pydantic.from_tortoise_orm(link.athlete) for link in linked]


@router.post("/")
async def add_athlete(
    athlete_id: int = Body(embed=True),
    coach: Coach = Depends(get_role(UserRoleEnum.COACH)),
):
    athlete = await Athlete.get(id=athlete_id)
    link = await CoachAthlete.filter(coach=coach, athlete=athlete).first()

    if not link:
        status = "pending"
    elif link.status == "rejected_coach":
        status = "accepted"
    else:
        return {"success": False, "status": link.status}

    await CoachAthlete.create(coach=coach, athlete=athlete, status=status)
    return {"success": True, "status": status}


@router.delete("/", status_code=204)
async def reject_athlete(
    athlete_id: int = Body(embed=True),
    coach: Coach = Depends(get_role(UserRoleEnum.COACH)),
):
    athlete = await Athlete.get(id=athlete_id)
    link = await CoachAthlete.filter(coach=coach, athlete=athlete).first()
    if not link:
        raise APIError(ErrorCode.ATHLETE_COACH_NOT_FOUND)

    link.status = "rejected_coach"
    await link.save()
