from fastapi import APIRouter, Depends

from app.core.security.deps.permissions import admin_required
from app.models.athlete.record import Record
from app.schemas.athlete.records import RecordIn, RecordOut

router = APIRouter(tags=['Admin/Record'])


@router.post("/", dependencies=[Depends(admin_required)], response_model=RecordOut)
async def create_record(data: RecordIn):
    await Record.filter(
        stroke=data.stroke,
        distance=data.distance,
        gender_age=data.gender_age,
        is_active=True,
    ).update(is_active=False)

    record = await Record.create(**data.model_dump(), is_active=True)
    return await RecordOut.from_tortoise_orm(record)
