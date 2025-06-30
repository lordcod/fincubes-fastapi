
from typing import List, Optional

from fastapi import APIRouter, Depends

from app.core.security.permissions import admin_required
from app.models.athlete.record import Record
from app.schemas.athlete.records import RecordIn, RecordOut

router = APIRouter()


@router.post("/", dependencies=[Depends(admin_required)], response_model=RecordOut)
async def create_record(data: RecordIn):
    await Record.filter(
        stroke=data.stroke,
        distance=data.distance,
        gender_age=data.gender_age,
        is_active=True,
    ).update(is_active=False)

    record = await Record.create(**data.dict(), is_active=True)
    return await RecordOut.from_tortoise_orm(record)


@router.get("/", response_model=List[RecordOut])
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
