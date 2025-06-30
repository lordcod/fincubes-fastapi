
from typing import List

from fastapi import APIRouter, Body, Depends

from app.core.errors import APIError, ErrorCode
from app.models.athlete.athlete import Athlete
from app.models.roles.parent import Parent
from app.schemas.athlete.athlete import Athlete_Pydantic
from app.shared.enums.enums import UserRoleEnum
from app.shared.utils.user_role import get_role

router = APIRouter()


@router.get("/", response_model=List[Athlete_Pydantic])
async def get_children(parent: Parent = Depends(get_role(UserRoleEnum.PARENT))):
    query = parent.athletes.all()
    return await Athlete_Pydantic.from_queryset(query)


@router.post("/", response_model=Athlete_Pydantic)
async def add_child(
    athlete_id: int = Body(embed=True),
    parent: Parent = Depends(get_role(UserRoleEnum.PARENT)),
):
    athlete = await Athlete.get(id=athlete_id)

    is_exists = await parent.athletes.filter(id=athlete_id).exists()
    if is_exists:
        raise APIError(ErrorCode.ALREADY_ADDED_ATHLETE)

    await parent.athletes.add(athlete)

    return await Athlete_Pydantic.from_tortoise_orm(athlete)
