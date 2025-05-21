from schemas.records import RecordIn, RecordOut
from models.models import Record
from tortoise.exceptions import IntegrityError
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from misc.security import admin_required

router = APIRouter(prefix='/record')


@router.post("/", dependencies=[Depends(admin_required)], response_model=RecordOut)
async def create_record(data: RecordIn):
    await Record.filter(
        stroke=data.stroke,
        distance=data.distance,
        gender_age=data.gender_age,
        is_active=True
    ).update(is_active=False)

    record = await Record.create(**data.dict(), is_active=True)
    return await RecordOut.from_tortoise_orm(record)


@router.get("/", response_model=List[RecordOut])
async def list_records(
    stroke: Optional[str] = None,
    distance: Optional[int] = None,
    gender: Optional[str] = None
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


@router.get("/{record_id}", response_model=RecordOut)
async def get_record(record_id: int):
    record = await Record.filter(id=record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return await RecordOut.from_tortoise_orm(record)
