from fastapi import APIRouter

from app.core.errors import APIError, ErrorCode
from app.models.misc.standard_category import StandardCategory
from app.schemas.results.standards import StandardOut

router = APIRouter()


@router.get("/", response_model=StandardOut)
async def get_standard(standard_id: int):
    standard = await StandardCategory.filter(id=standard_id).first()
    if not standard:
        raise APIError(ErrorCode.STANDARD_NOT_FOUND, status_code=404)
    return await StandardOut.from_tortoise_orm(standard)
