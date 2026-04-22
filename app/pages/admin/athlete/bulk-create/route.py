from fastapi import APIRouter, Depends

from app.models.athlete.athlete import Athlete
from app.schemas.athlete.review import (
    BulkAthleteCreateRequest,
    BulkAthleteCreateResponse,
    BulkAthleteCreateResultItem,
)
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.post(
    "/",
    response_model=BulkAthleteCreateResponse,
)
@require_scope("athlete:create")
async def bulk_create_athletes(payload: BulkAthleteCreateRequest):
    created_models = [
        Athlete(
            last_name=item.last_name,
            first_name=item.first_name,
            birth_year=str(item.birth_year),
            gender=item.gender.upper(),
            city=item.city,
            club=item.club,
            license=item.license,
        )
        for item in payload.items
    ]

    if created_models:
        await Athlete.bulk_create(created_models)

    response_items = [
        BulkAthleteCreateResultItem(
            external_id=input_item.external_id,
            athlete=created_athlete,
        )
        for input_item, created_athlete in zip(payload.items, created_models)
    ]
    return BulkAthleteCreateResponse(items=response_items)
