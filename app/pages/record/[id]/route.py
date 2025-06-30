from fastapi import APIRouter

from app.core.errors import APIError, ErrorCode
from app.models.athlete.record import Record
from app.schemas.athlete.records import RecordOut

router = APIRouter()


@router.get("/", response_model=RecordOut)
async def get_record(id: int):
    record = await Record.filter(id=id).first()
    if not record:
        raise APIError(ErrorCode.RECORD_NOT_FOUND)
    return await RecordOut.from_tortoise_orm(record)
