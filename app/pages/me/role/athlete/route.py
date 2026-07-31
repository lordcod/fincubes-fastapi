
from fastapi import APIRouter, Body, Depends

from app.core.errors import APIError, ErrorCode
from app.models.athlete.athlete import Athlete
from app.schemas.athlete.athlete import Athlete_Pydantic
from app.services.location_catalog import get_or_create_location_object_by_identity
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
    current_location = None
    if athlete.location_object_id is not None:
        current_location = await athlete.location_object
    if current_location is None or not current_location.region:
        raise APIError(ErrorCode.LOCATION_REGION_REQUIRED)

    location = await get_or_create_location_object_by_identity(
        club=club.strip() or None,
        city=current_location.city,
        region=current_location.region,
    )
    athlete.location_object = location
    await athlete.save()
    return await Athlete_Pydantic.from_tortoise_orm(athlete)
