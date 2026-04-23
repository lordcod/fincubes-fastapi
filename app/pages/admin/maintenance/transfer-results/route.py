from fastapi import APIRouter, Depends

from app.pages.admin.maintenance.deps import require_maintenance_api_enabled
from app.schemas.admin.maintenance import TransferResultsRequest
from app.services.admin_maintenance import TransferResultsResult, transfer_results
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.post(
    "/",
    response_model=TransferResultsResult,
)
@require_scope("maintenance:write")
async def transfer_results_endpoint(
    payload: TransferResultsRequest,
    _: None = Depends(require_maintenance_api_enabled),
):
    return await transfer_results(
        from_athlete_id=payload.from_athlete_id,
        to_athlete_id=payload.to_athlete_id,
        competition_id=payload.competition_id,
        apply=payload.apply,
        delete_empty_source=payload.delete_empty_source,
    )
