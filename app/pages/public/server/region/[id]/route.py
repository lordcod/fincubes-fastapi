from fastapi import APIRouter

from app.core.errors import APIError, ErrorCode
from app.models.misc.region import Region
from app.schemas.region.region import RegionOut
from app.shared.clients.scopes.request import require_scope

router = APIRouter()


@router.get("/", response_model=RegionOut)
@require_scope('region:read')
async def get_region(id: int):
    standard = await Region.get(id=id)
    return await RegionOut.from_tortoise_orm(standard)
