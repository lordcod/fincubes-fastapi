
from typing import List

from fastapi import APIRouter
from tortoise.expressions import Q

from app.models.athlete.athlete import Athlete
from app.schemas.athlete.athlete import Athlete_Pydantic

router = APIRouter(tags=['Public/Athlete'])


@router.get("/", response_model=List[Athlete_Pydantic])
async def get_athletes(
    query: str = None,
    last_name: str = None,
    first_name: str = None,
    birth_year: int = None,
    club: str = None,
    gender: str = None,
    limit: int = None,
):

    q_filter = Q()

    if query:
        limit = limit if limit is not None else 15

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

    if last_name:
        q_filter &= Q(last_name__icontains=last_name)
    if first_name:
        q_filter &= Q(first_name__icontains=first_name)
    if birth_year:
        q_filter &= Q(birth_year=birth_year)
    if club:
        q_filter &= Q(club__icontains=club)
    if gender:
        q_filter &= Q(gender=gender)

    if limit is None:
        athletes = await Athlete.filter(q_filter)
    else:
        athletes = await Athlete.filter(q_filter).limit(limit)
    return athletes
