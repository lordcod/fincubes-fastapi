from fastapi import APIRouter

from app.schemas.admin.protocol_import import ProtocolImportRequest
from app.services.protocol_import import process_protocol_import
from app.shared.utils.scopes.request import require_scope

router = APIRouter(tags=["Admin/Protocol import"])


@router.post("/")
@require_scope("protocol:import")
async def import_protocol(payload: ProtocolImportRequest):
    return await process_protocol_import(payload)
