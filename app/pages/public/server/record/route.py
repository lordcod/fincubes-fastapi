
from typing import List, Optional

from fastapi import APIRouter

from app.models.athlete.record import Record
from app.schemas.athlete.records import RecordOut
from app.shared.clients.scopes.request import require_scope

router = APIRouter(tags=['Public/Server/Record'])


@router.get("/", response_model=List[RecordOut])
@require_scope('record:read')
async def list_records(
    stroke: Optional[str] = None,
    distance: Optional[int] = None,
    gender: Optional[str] = None,
):
    filters = {"is_active": True}

    if stroke:
        filters["stroke"] = stroke
    if distance:
        filters["distance"] = distance
    if gender:
        filters["gender"] = gender

    records = Record.filter(**filters)
    return await RecordOut.from_queryset(records)
