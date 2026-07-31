
from typing import List

from fastapi import APIRouter
from tortoise.expressions import Q


from app.models.athlete.athlete import Athlete
from app.schemas.athlete.athlete import (
    AthleteCreateRequest,
    Athlete_Pydantic,
)
from app.services.location_catalog import resolve_athlete_location_object
from app.shared.utils.scopes.request import require_scope

router = APIRouter(tags=['Admin/Athlete'])


@router.get(
    "/",
    response_model=List[Athlete_Pydantic],
)
@require_scope('athlete:read')
async def get_athletes_admin(
    query: str = None,
    last_name: str = None,
    first_name: str = None,
    birth_year: int = None,
    club: str = None,
    city: str = None,
    region: str = None,
    gender: str = None,
    limit: int = None
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
            q_filter |= (Q(last_name__icontains=a) &
                         Q(first_name__icontains=b))
            q_filter |= (Q(last_name__icontains=b) &
                         Q(first_name__icontains=a))

        elif len(parts) == 3:
            a, b, c = parts
            if c.isdigit():
                q_filter |= (Q(last_name__icontains=a) & Q(
                    first_name__icontains=b) & Q(birth_year=int(c)))
                q_filter |= (Q(last_name__icontains=b) & Q(
                    first_name__icontains=a) & Q(birth_year=int(c)))
            else:
                q_filter |= (Q(last_name__icontains=a) & Q(
                    first_name__icontains=f"{b} {c}"))
                q_filter |= (Q(last_name__icontains=b) & Q(
                    first_name__icontains=f"{a} {c}"))

    if last_name:
        q_filter &= Q(last_name__icontains=last_name)
    if first_name:
        q_filter &= Q(first_name__icontains=first_name)
    if birth_year:
        q_filter &= Q(birth_year=birth_year)
    if club:
        q_filter &= Q(location_object__club__icontains=club)
    if city:
        q_filter &= Q(location_object__city__icontains=city)
    if region:
        q_filter &= Q(location_object__region__icontains=region)
    if gender:
        q_filter &= Q(gender=gender)

    if limit is None:
        athletes = await Athlete.filter(q_filter)
    else:
        athletes = await Athlete.filter(q_filter).limit(limit)
    return await Athlete_Pydantic.from_queryset(athletes)


@router.post(
    "/",
    response_model=Athlete_Pydantic
)
@require_scope('athlete:create')
async def create_athlete(athlete: AthleteCreateRequest):
    athlete_data = athlete.model_dump()
    location_alias = athlete_data.pop("alias", None)
    club = athlete_data.pop("club", None)
    city = athlete_data.pop("city", None)
    region = athlete_data.pop("region", None)
    athlete_data["birth_year"] = str(athlete_data["birth_year"])
    location = await resolve_athlete_location_object(
        alias=location_alias,
        club=club,
        city=city,
        region=region,
    )
    db_athlete = await Athlete.create(
        **athlete_data,
        location_object=location,
    )
    return await Athlete_Pydantic.from_tortoise_orm(db_athlete)
