
from typing import List

from fastapi import APIRouter, Depends
from tortoise.expressions import Q
from tortoise.transactions import in_transaction


from app.models.athlete.athlete import Athlete
from app.models.location.athlete_location import AthleteLocation
from app.schemas.athlete.athlete import (
    AthleteCreateRequest,
    Athlete_Pydantic,
)
from app.services.location_catalog import (
    legacy_club_value,
    resolve_location_link,
)
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
        q_filter &= Q(club__icontains=club)
    if gender:
        q_filter &= Q(gender=gender)

    if limit is None:
        athletes = await Athlete.filter(q_filter)
    else:
        athletes = await Athlete.filter(q_filter).limit(limit)
    return athletes


@router.post(
    "/",
    response_model=Athlete_Pydantic
)
@require_scope('athlete:create')
async def create_athlete(athlete: AthleteCreateRequest):
    location_object = (
        await resolve_location_link(athlete.location)
        if athlete.location is not None
        else None
    )
    athlete_data = athlete.model_dump(exclude={"location"})
    athlete_data["birth_year"] = str(athlete_data["birth_year"])
    if location_object is not None:
        athlete_data["club"] = athlete_data["club"] or legacy_club_value(
            athlete.location.alias,
            location_object.club,
        )
        athlete_data["city"] = athlete_data["city"] or location_object.city

    async with in_transaction() as connection:
        db_athlete = await Athlete.create(
            **athlete_data,
            using_db=connection,
        )
        if location_object is not None:
            await AthleteLocation.create(
                athlete=db_athlete,
                location_object=location_object,
                alias=athlete.location.alias,
                using_db=connection,
            )
    return db_athlete
