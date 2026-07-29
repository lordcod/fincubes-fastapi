from fastapi import APIRouter, status

from app.schemas.results.relay import RelayResultWithLegs
from app.services.relay_results import (
    delete_relay_result,
    get_relay_result,
)
from app.shared.utils.scopes.request import require_scope

router = APIRouter(tags=["Admin/Relay results"])


@router.get(
    "/",
    response_model=RelayResultWithLegs,
)
@require_scope("result:read")
async def get_relay_result_endpoint(id: int):
    return await get_relay_result(id)


@router.delete(
    "/",
    status_code=status.HTTP_204_NO_CONTENT,
)
@require_scope("result:delete")
async def delete_relay_result_endpoint(id: int):
    await delete_relay_result(id)
