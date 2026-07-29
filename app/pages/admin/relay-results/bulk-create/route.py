from fastapi import APIRouter, status

from app.schemas.results.relay import (
    RelayResultCreate,
    RelayResultWithLegs,
)
from app.services.relay_results import bulk_create_relay_results
from app.shared.utils.scopes.request import require_scope

router = APIRouter(tags=["Admin/Relay results"])


@router.post(
    "/",
    response_model=list[RelayResultWithLegs],
    status_code=status.HTTP_201_CREATED,
)
@require_scope("result:create")
async def bulk_create_relay_results_endpoint(
    payloads: list[RelayResultCreate],
):
    return await bulk_create_relay_results(payloads)
