
from typing import List

from fastapi import APIRouter, Depends


from app.models.misc.region import Region
from app.schemas.region.region import RegionIn, RegionOut
from app.shared.utils.scopes.request import require_scope

router = APIRouter(tags=['Public/Server/Region'])


@router.get("/", response_model=List[RegionOut])
@require_scope('region:read')
async def list_regions():
    query = Region.all()
    return await RegionOut.from_queryset(query)
