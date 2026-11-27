from uuid import UUID
from fastapi import APIRouter

from app.schemas.admin.protocol_import import ProtocolImportRequest
from app.services.protocol_import import process_protocol_import, get_protocol_import
from app.shared.utils.scopes.request import require_scope

router = APIRouter(tags=["Admin/Protocol import"])


@router.post("/")
@require_scope("protocol:import")
async def import_protocol(payload: ProtocolImportRequest):
    return await process_protocol_import(payload)


@router.get("/{import_id}/")
@require_scope("protocol:import")
async def protocol_import_state(import_id: UUID):
    return await get_protocol_import(import_id)
