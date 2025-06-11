from typing import List
from fastapi import APIRouter, Body, Depends
from misc.errors import APIError, ErrorCode
from models.models import Athlete, Coach, CoachAthlete
from models.enums import UserRoleEnum
from routers.users.utils import get_role
from schemas.athlete import Athlete_Pydantic
from schemas.users.coach import CoachIn, CoachOut

router = APIRouter(prefix="/coaches")


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


@router.get("/athletes/", response_model=List[Athlete_Pydantic])
async def get_athletes(coach: Coach = Depends(get_role(UserRoleEnum.COACH))):
    linked = await CoachAthlete.filter(coach=coach).select_related("athlete")
    return [await Athlete_Pydantic.from_tortoise_orm(link.athlete) for link in linked]


@router.post("/athletes/")
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


@router.delete("/athletes/", status_code=204)
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
