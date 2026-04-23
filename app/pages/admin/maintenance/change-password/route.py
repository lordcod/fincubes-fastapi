from fastapi import APIRouter, Depends

from app.pages.admin.maintenance.deps import require_maintenance_api_enabled
from app.schemas.admin.maintenance import ChangePasswordRequest
from app.services.admin_maintenance import ChangePasswordResult, change_password
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.post(
    "/",
    response_model=ChangePasswordResult,
)
@require_scope("maintenance:write")
async def change_password_endpoint(
    payload: ChangePasswordRequest,
    _: None = Depends(require_maintenance_api_enabled),
):
    return await change_password(
        user_id=payload.user_id,
        new_password=payload.new_password,
        apply=payload.apply,
    )
