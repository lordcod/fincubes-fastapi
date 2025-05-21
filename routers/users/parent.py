from tkinter.tix import Tree
from typing import List, Optional
from fastapi import APIRouter, Body, HTTPException, Depends
from tortoise.exceptions import DoesNotExist
from misc.errors import APIError, ErrorCode
from models.models import Athlete, Parent, User, UserParent
from misc.security import get_current_user
from schemas.athlete import Athlete_Pydantic


async def get_parent(
    user: User = Depends(get_current_user)
) -> Parent:
    if user.role != 'parent':
        raise APIError(ErrorCode.INVALID_ROLE)
    parent = await UserParent.filter(user=user).first().select_related('parent')
    return parent.parent

router = APIRouter(
    prefix='/parent')


@router.get('/children', response_model=List[Athlete_Pydantic])
async def get_children(parent: Parent = Depends(get_parent)):
    query = parent.athletes.all()
    return await Athlete_Pydantic.from_queryset(query)


@router.post('/children/', response_model=Athlete_Pydantic)
async def add_child(athlete_id: int = Body(embed=True), parent: Parent = Depends(get_parent)):
    athlete = await Athlete.get(id=athlete_id)

    is_exists = await parent.athletes.filter(id=athlete_id).exists()
    if is_exists:
        raise APIError(ErrorCode.ALREADY_ADDED_ATHLETE)

    await parent.athletes.add(athlete)

    return await Athlete_Pydantic.from_tortoise_orm(athlete)
