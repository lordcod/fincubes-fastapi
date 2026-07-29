from fastapi import APIRouter, Depends

from app.core.errors import APIError, ErrorCode
from app.models.athlete.athlete import Athlete
from app.models.location.athlete_location import AthleteLocation
from app.schemas.location.location import AthleteLocationOut, LocationObjectOut
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.get("/", response_model=list[AthleteLocationOut])
@require_scope("athlete:read")
async def get_athlete_locations(athlete_id: int):
    if not await Athlete.filter(id=athlete_id).exists():
        raise APIError(ErrorCode.ATHLETE_NOT_FOUND)

    links = await AthleteLocation.filter(
        athlete_id=athlete_id
    ).select_related("location_object")
    return [
        AthleteLocationOut(
            id=link.id,
            athlete_id=link.athlete_id,
            alias=link.alias,
            location=LocationObjectOut.model_validate(link.location_object),
        )
        for link in links
    ]
