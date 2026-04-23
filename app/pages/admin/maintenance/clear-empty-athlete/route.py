from fastapi import APIRouter, Depends

from app.pages.admin.maintenance.deps import require_maintenance_api_enabled
from app.schemas.admin.maintenance import ClearEmptyAthletesRequest
from app.services.admin_maintenance import MaintenanceOperationResult, clear_empty_athletes
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.post(
    "/",
    response_model=MaintenanceOperationResult,
)
@require_scope("maintenance:write")
async def clear_empty_athlete_endpoint(
    payload: ClearEmptyAthletesRequest,
    _: None = Depends(require_maintenance_api_enabled),
):
    return await clear_empty_athletes(apply=payload.apply)
