
from fastapi import APIRouter, Body, Depends

from app.core.errors import APIError, ErrorCode
from app.models.athlete.athlete import Athlete
from app.schemas.athlete.athlete import Athlete_Pydantic
from app.shared.enums.enums import UserRoleEnum
from app.shared.utils.user_role import get_role

router = APIRouter(tags=['Me/Role/Athlete'])


@router.get("/", response_model=Athlete_Pydantic)
async def get_athlete_me(athlete: Athlete = Depends(get_role(UserRoleEnum.ATHLETE))):
    return await Athlete_Pydantic.from_tortoise_orm(athlete)


@router.put("/", response_model=Athlete_Pydantic)
async def edit_athlete_me(
    club: str = Body(embed=True),
    athlete: Athlete = Depends(get_role(UserRoleEnum.ATHLETE)),
):
    athlete.club = club.strip() or None
    athlete.location_object_id = None
    await athlete.save()
    return await Athlete_Pydantic.from_tortoise_orm(athlete)
