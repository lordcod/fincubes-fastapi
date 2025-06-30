
from typing import Optional

from fastapi import APIRouter, Body, Depends

from app.models.athlete.athlete import Athlete
from app.schemas.athlete.athlete import Athlete_Pydantic
from app.shared.enums.enums import UserRoleEnum
from app.shared.utils.user_role import get_role

router = APIRouter()


@router.get("/", response_model=Athlete_Pydantic)
async def get_athlete_me(athlete: Athlete = Depends(get_role(UserRoleEnum.ATHLETE))):
    return await Athlete_Pydantic.from_tortoise_orm(athlete)


@router.put("/", response_model=Athlete_Pydantic)
async def edit_athlete_me(
    club: Optional[str] = Body(embed=True, default=None),
    athlete: Athlete = Depends(get_role(UserRoleEnum.ATHLETE)),
):
    athlete.club = club
    await athlete.save()
    return await Athlete_Pydantic.from_tortoise_orm(athlete)
