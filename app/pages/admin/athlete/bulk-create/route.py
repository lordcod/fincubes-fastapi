from fastapi import APIRouter
from tortoise.transactions import in_transaction

from app.models.athlete.athlete import Athlete
from app.schemas.athlete.bulk import (
    BulkAthleteCreateRequest,
    BulkAthleteCreateResponse,
    BulkAthleteCreateResultItem,
)
from app.schemas.athlete.athlete import Athlete_Pydantic
from app.services.athlete_affiliation import athlete_text_fields
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
            data = await athlete_text_fields(item.model_dump(exclude={"external_id"}))
            data["birth_year"] = str(data["birth_year"])
            data["gender"] = data["gender"].upper()
            athlete = await Athlete.create(**data, using_db=connection)
            created_models.append(athlete)

    response_items = [
        BulkAthleteCreateResultItem(
            external_id=input_item.external_id,
            athlete=await Athlete_Pydantic.from_tortoise_orm(created_athlete),
        )
        for input_item, created_athlete in zip(payload.items, created_models)
    ]
    return BulkAthleteCreateResponse(items=response_items)
