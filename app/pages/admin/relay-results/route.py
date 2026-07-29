from fastapi import APIRouter, Query, status

from app.schemas.results.relay import (
    RelayResultCreate,
    RelayResultWithLegs,
)
from app.services.relay_results import (
    create_relay_result,
    list_relay_results,
)
from app.shared.enums.enums import GenderEnum
from app.shared.utils.scopes.request import require_scope

router = APIRouter(tags=["Admin/Relay results"])


@router.post(
    "/",
    response_model=RelayResultWithLegs,
    status_code=status.HTTP_201_CREATED,
)
@require_scope("result:create")
async def create_relay_result_endpoint(
    payload: RelayResultCreate,
):
    return await create_relay_result(payload)


@router.get(
    "/",
    response_model=list[RelayResultWithLegs],
)
@require_scope("result:read")
async def list_relay_results_endpoint(
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
