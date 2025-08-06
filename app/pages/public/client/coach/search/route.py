
from typing import List

from fastapi import APIRouter, Depends
from tortoise.expressions import Q


from app.models.roles.coach import Coach
from app.schemas.users.coach import CoachOut
from app.shared.clients.scopes.request import require_scope

router = APIRouter(tags=['Public/Client/Coach'])


@router.get("/", response_model=List[CoachOut])
@require_scope('client.coach:read')
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
