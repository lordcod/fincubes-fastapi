from fastapi import APIRouter

from app.core.errors import APIError, ErrorCode
from app.models.misc.region import Region
from app.schemas.region.region import RegionOut

router = APIRouter()


@router.get("/", response_model=RegionOut)
async def get_region(id: int):
    standard = await Region.get(id=id)
    if not standard:
        raise APIError(ErrorCode.STANDARD_NOT_FOUND, status_code=404)
    return await RegionOut.from_tortoise_orm(standard)
