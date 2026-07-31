from fastapi import APIRouter
from tortoise.transactions import in_transaction

from app.models.athlete.athlete import Athlete
from app.schemas.athlete.bulk import (
    BulkAthleteCreateRequest,
    BulkAthleteCreateResponse,
    BulkAthleteCreateResultItem,
)
from app.services.location_catalog import resolve_athlete_location_fields
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.post(
    "/",
    response_model=BulkAthleteCreateResponse,
)
@require_scope("athlete:create")
async def bulk_create_athletes(payload: BulkAthleteCreateRequest):
    created_models: list[Athlete] = []

    async with in_transaction() as connection:
        for item in payload.items:
            location_fields = await resolve_athlete_location_fields(
                alias=item.alias,
                club=item.club,
                city=item.city,
                region=item.region,
            )
            athlete = await Athlete.create(
                last_name=item.last_name,
                first_name=item.first_name,
                birth_year=str(item.birth_year),
                gender=item.gender.upper(),
                city=location_fields["city"],
                region=location_fields["region"],
                club=location_fields["club"],
                license=item.license,
                using_db=connection,
            )
            created_models.append(athlete)

    response_items = [
        BulkAthleteCreateResultItem(
            external_id=input_item.external_id,
            athlete=created_athlete,
        )
        for input_item, created_athlete in zip(payload.items, created_models)
    ]
    return BulkAthleteCreateResponse(items=response_items)
