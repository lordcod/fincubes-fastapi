
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends

from app.core.errors import APIError, ErrorCode
from app.models.athlete.athlete import Athlete
from app.models.location.location_object import LocationObject
from app.schemas.athlete.athlete import Athlete_Pydantic
from app.shared.enums.enums import UserRoleEnum
from app.shared.utils.user_role import get_role

router = APIRouter(tags=['Me/Role/Athlete'])


@router.get("/", response_model=Athlete_Pydantic)
async def get_athlete_me(athlete: Athlete = Depends(get_role(UserRoleEnum.ATHLETE))):
    return await Athlete_Pydantic.from_tortoise_orm(athlete)


@router.put("/", response_model=Athlete_Pydantic)
async def edit_athlete_me(
    location_object_id: Optional[UUID] = Body(embed=True, default=None),
    athlete: Athlete = Depends(get_role(UserRoleEnum.ATHLETE)),
):
    if location_object_id is not None:
        location_exists = await LocationObject.filter(id=location_object_id).exists()
        if not location_exists:
            raise APIError(ErrorCode.LOCATION_OBJECT_NOT_FOUND)
    athlete.location_object_id = location_object_id
    await athlete.save()
    return await Athlete_Pydantic.from_tortoise_orm(athlete)
