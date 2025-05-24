from typing import List

from fastapi import APIRouter
from models.models import Athlete, Coach, CoachAthlete
from schemas.users.coach import CoachOut
from tortoise.expressions import Q

router = APIRouter(
    prefix='/coaches', tags=['coaches'])


@router.get('/search/', response_model=List[CoachOut])
async def search_coach(q: str):
    if not q.strip():
        return []

    words = q.strip().split()

    query = Q()
    for word in words:
        part = (
            Q(last_name__icontains=word) |
            Q(first_name__icontains=word) |
            Q(middle_name__icontains=word) |
            Q(city__icontains=word) |
            Q(club__icontains=word)
        )
        query &= part

    coaches = Coach.filter(query)
    return await CoachOut.from_queryset(coaches)


@router.get('/{id}', response_model=CoachOut)
async def get_coach_from_id(id: int):
    coach = await Coach.get(id=id)
    return await CoachOut.from_tortoise_orm(coach)


@router.get('/athlete/{athlete_id}',
            response_model=List[CoachOut])
async def get_coaches_athlete(athlete_id: int):
    athlete = await Athlete.get(id=athlete_id)
    linked = await CoachAthlete.filter(athlete=athlete).select_related('coach')
    return [await CoachOut.from_tortoise_orm(link.coach)
            for link in linked]
