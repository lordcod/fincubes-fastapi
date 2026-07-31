from fastapi import APIRouter

from app.core.errors import APIError, ErrorCode
from app.models.athlete.athlete import Athlete
from app.schemas.location.location import LocationObjectOut
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.get("/", response_model=dict)
@require_scope("athlete:read")
async def get_athlete_locations(athlete_id: int):
    athlete = await Athlete.get_or_none(id=athlete_id).prefetch_related("location_object")
    if athlete is None:
        raise APIError(ErrorCode.ATHLETE_NOT_FOUND)
    location = None
    if athlete.location_object_id is not None:
        location = LocationObjectOut.model_validate(await athlete.location_object)
    return {
        "athlete_id": athlete.id,
        "location_object_id": athlete.location_object_id,
        "location": location,
        "club": location.club if location else None,
        "city": location.city if location else None,
        "region": location.region if location else None,
    }
