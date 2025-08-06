
from typing import List

from fastapi import APIRouter, Depends
from tortoise.expressions import Q


from app.models.athlete.athlete import Athlete
from app.schemas.athlete.athlete import Athlete_Pydantic
from app.shared.clients.scopes.request import require_scope

router = APIRouter(tags=['Public/Client/Athlete'])


@router.get("/", response_model=List[Athlete_Pydantic])
@require_scope('client.athlete:read')
async def get_athletes(
    query: str,
    limit: int = 15,
):

    q_filter = Q()

    if query:
        parts = query.strip().split()
        if len(parts) == 1:
            term = parts[0]
            q_filter |= Q(last_name__icontains=term)
            q_filter |= Q(first_name__icontains=term)
            if term.isdigit():
                q_filter |= Q(birth_year=int(term))

        elif len(parts) == 2:
            a, b = parts
            q_filter |= Q(last_name__icontains=a) & Q(first_name__icontains=b)
            q_filter |= Q(last_name__icontains=b) & Q(first_name__icontains=a)

        elif len(parts) == 3:
            a, b, c = parts
            if c.isdigit():
                q_filter |= (
                    Q(last_name__icontains=a)
                    & Q(first_name__icontains=b)
                    & Q(birth_year=int(c))
                )
                q_filter |= (
                    Q(last_name__icontains=b)
                    & Q(first_name__icontains=a)
                    & Q(birth_year=int(c))
                )
            else:
                q_filter |= Q(last_name__icontains=a) & Q(
                    first_name__icontains=f"{b} {c}"
                )
                q_filter |= Q(last_name__icontains=b) & Q(
                    first_name__icontains=f"{a} {c}"
                )

    if limit is None:
        athletes = await Athlete.filter(q_filter)
    else:
        athletes = await Athlete.filter(q_filter).limit(limit)
    return athletes
