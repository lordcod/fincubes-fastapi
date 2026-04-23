from fastapi import APIRouter, Depends

from app.pages.admin.maintenance.deps import require_maintenance_api_enabled
from app.schemas.admin.maintenance import CompetitionMaintenanceRequest
from app.services.admin_maintenance import MaintenanceOperationResult, clear_distances
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.post(
    "/",
    response_model=MaintenanceOperationResult,
)
@require_scope("maintenance:write")
async def clear_distances_endpoint(
    payload: CompetitionMaintenanceRequest,
    _: None = Depends(require_maintenance_api_enabled),
):
    return await clear_distances(competition_id=payload.competition_id, apply=payload.apply)
