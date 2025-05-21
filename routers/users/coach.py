from tkinter.tix import Tree
from typing import List, Optional
from fastapi import APIRouter, Body, HTTPException, Depends
from tortoise.exceptions import DoesNotExist
from misc.errors import APIError, ErrorCode
from models.models import Athlete, Coach, CoachAthlete, Parent, User, UserCoach, UserParent
from misc.security import get_current_user
from schemas.athlete import Athlete_Pydantic


async def get_coach(
    user: User = Depends(get_current_user)
) -> Coach:
    if user.role != 'coach':
        raise APIError(ErrorCode.INVALID_ROLE)
    parent = await UserCoach.filter(user=user).first().select_related('coach')
    return parent.coach

router = APIRouter(
    prefix='/coach')


@router.get('/athletes/', response_model=List[Athlete_Pydantic])
async def get_althlete(coach: Coach = Depends(get_coach)):
    linked = await CoachAthlete.filter(
        coach=coach).select_related('athlete').only('athlete')
    return [await Athlete_Pydantic.from_tortoise_orm(link.athlete)
            for link in linked]


@router.post('/athletes/', response_model=Athlete_Pydantic)
async def add_child(athlete_id: int = Body(embed=True), parent: Parent = Depends(get_coach)):
    athlete = await Athlete.get(id=athlete_id)

    is_exists = await parent.athletes.filter(id=athlete_id).exists()
    if is_exists:
        raise APIError(ErrorCode.ALREADY_ADDED_ATHLETE)

    await parent.athletes.add(athlete)

    return await Athlete_Pydantic.from_tortoise_orm(athlete)
