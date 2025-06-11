from typing import List
from fastapi import APIRouter, Body, Depends
from misc.errors import APIError, ErrorCode
from models.models import Athlete, Parent
from models.enums import UserRoleEnum
from routers.users.utils import get_role
from schemas.athlete import Athlete_Pydantic

router = APIRouter(prefix="/parent")


@router.get("/children", response_model=List[Athlete_Pydantic])
async def get_children(parent: Parent = Depends(get_role(UserRoleEnum.PARENT))):
    query = parent.athletes.all()
    return await Athlete_Pydantic.from_queryset(query)


@router.post("/children/", response_model=Athlete_Pydantic)
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
