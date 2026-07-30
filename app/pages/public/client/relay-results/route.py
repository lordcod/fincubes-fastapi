from fastapi import APIRouter, Query

from app.schemas.results.relay import RelayResultWithLegs
from app.services.relay_results import list_relay_results
from app.shared.enums.enums import GenderEnum
from app.shared.utils.scopes.request import require_scope

router = APIRouter(tags=["Public/Client/Relay results"])


@router.get("/", response_model=list[RelayResultWithLegs])
@require_scope("client.result:read")
async def list_client_relay_results(
    competition_id: int,
    stroke: str | None = None,
    distance: int | None = Query(default=None, gt=0),
    relay_count: int | None = Query(default=None, gt=1),
    gender: GenderEnum | None = None,
):
    return await list_relay_results(
        competition_id=competition_id,
        stroke=stroke,
        distance=distance,
        relay_count=relay_count,
        gender=gender,
    )
