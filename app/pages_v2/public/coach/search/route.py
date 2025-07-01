
from typing import List

from fastapi import APIRouter
from tortoise.expressions import Q

from app.models.roles.coach import Coach
from app.schemas.users.coach import CoachOut

router = APIRouter()


@router.get("/", response_model=List[CoachOut])
async def search_coach(q: str):
    if not q.strip():
        return []

    words = q.strip().split()

    query = Q()
    for word in words:
        part = (
            Q(last_name__icontains=word)
            | Q(first_name__icontains=word)
            | Q(middle_name__icontains=word)
            | Q(city__icontains=word)
            | Q(club__icontains=word)
        )
        query &= part

    coaches = Coach.filter(query)
    return await CoachOut.from_queryset(coaches)
