from fastapi import APIRouter

from app.core.errors import APIError, ErrorCode
from app.models.misc.standard_category import StandardCategory
from app.schemas.results.standards import StandardOut

router = APIRouter(tags=['Internal/Standard'])


@router.get("/", response_model=StandardOut)
async def get_standard(id: int):
    standard = await StandardCategory.filter(id=id).first()
    if not standard:
        raise APIError(ErrorCode.STANDARD_NOT_FOUND)
    return await StandardOut.from_tortoise_orm(standard)
