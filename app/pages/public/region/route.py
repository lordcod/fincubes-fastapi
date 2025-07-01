
from typing import List

from fastapi import APIRouter, Depends

from app.core.security.permissions import admin_required
from app.models.misc.region import Region
from app.schemas.region.region import RegionIn, RegionOut

router = APIRouter(tags=['Public/Region'])


@router.get("/", response_model=List[RegionOut])
async def list_regions():
    query = Region.all()
    return await RegionOut.from_queryset(query)
