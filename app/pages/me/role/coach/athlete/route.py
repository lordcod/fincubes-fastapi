

from typing import List

from fastapi import APIRouter, Body, Depends

from app.core.errors import APIError, ErrorCode
from app.models.athlete.athlete import Athlete
from app.models.roles.coach import Coach
from app.models.roles.coach_athlete import CoachAthlete
from app.schemas.athlete.athlete import Athlete_Pydantic, AthleteWithStatus_Pydantic
from app.shared.enums.enums import CoachAthleteStatusEnum, UserRoleEnum
from app.shared.utils.user_role import get_role

router = APIRouter()


@router.get("/", response_model=List[AthleteWithStatus_Pydantic])
async def get_athletes(coach: Coach = Depends(get_role(UserRoleEnum.COACH))):
    linked = await CoachAthlete.filter(coach=coach).prefetch_related("athlete")

    results = []
    for link in linked:
        athlete_data = await Athlete_Pydantic.from_tortoise_orm(link.athlete)
        athlete = athlete_data.model_dump()
        athlete['status'] = link.status
        results.append(athlete)

    return results


@router.post("/")
async def add_athlete(
    athlete_id: int = Body(embed=True),
    coach: Coach = Depends(get_role(UserRoleEnum.COACH)),
):
    athlete = await Athlete.get(id=athlete_id)
    link = await CoachAthlete.filter(coach=coach, athlete=athlete).first()

    if not link:
        status = CoachAthleteStatusEnum.PENDING
    elif link.status == CoachAthleteStatusEnum.REJECTED_COACH:
        status = CoachAthleteStatusEnum.ACCEPTED
    else:
        return {"success": False, "status": link.status}

    if link:
        link.status = status
        await link.save()
    else:
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
    if link.status == CoachAthleteStatusEnum.REJECTED_ATHLETE:
        return

    link.status = CoachAthleteStatusEnum.REJECTED_COACH
    await link.save()
