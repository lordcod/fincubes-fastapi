from fastapi import APIRouter, Depends
from tortoise.transactions import in_transaction

from app.models.athlete.athlete import Athlete
from app.models.location.athlete_location import AthleteLocation
from app.schemas.athlete.bulk import (
    BulkAthleteCreateRequest,
    BulkAthleteCreateResponse,
    BulkAthleteCreateResultItem,
)
from app.services.location_catalog import (
    legacy_club_value,
    resolve_location_link,
)
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.post(
    "/",
    response_model=BulkAthleteCreateResponse,
)
@require_scope("athlete:create")
async def bulk_create_athletes(payload: BulkAthleteCreateRequest):
    resolved_locations = [
        (
            await resolve_location_link(item.location)
            if item.location is not None
            else None
        )
        for item in payload.items
    ]
    created_models: list[Athlete] = []

    async with in_transaction() as connection:
        for item, location_object in zip(
            payload.items,
            resolved_locations,
        ):
            athlete = await Athlete.create(
                last_name=item.last_name,
                first_name=item.first_name,
                birth_year=str(item.birth_year),
                gender=item.gender.upper(),
                city=item.city or (
                    location_object.city if location_object is not None else None
                ),
                club=item.club or (
                    legacy_club_value(
                        item.location.alias,
                        location_object.club,
                    )
                    if item.location is not None
                    else None
                ),
                license=item.license,
                using_db=connection,
            )
            created_models.append(athlete)

            if location_object is not None and item.location is not None:
                await AthleteLocation.create(
                    athlete=athlete,
                    location_object=location_object,
                    alias=item.location.alias,
                    using_db=connection,
                )

    response_items = [
        BulkAthleteCreateResultItem(
            external_id=input_item.external_id,
            athlete=created_athlete,
        )
        for input_item, created_athlete in zip(payload.items, created_models)
    ]
    return BulkAthleteCreateResponse(items=response_items)
