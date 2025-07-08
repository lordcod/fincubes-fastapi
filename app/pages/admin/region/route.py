
from typing import List

from fastapi import APIRouter, Depends

from app.core.security.deps.permissions import admin_required
from app.models.misc.region import Region
from app.schemas.region.region import RegionIn, RegionOut

router = APIRouter(tags=['Admin/Region'])


@router.post("/", dependencies=[Depends(admin_required)], response_model=RegionOut)
async def create_region(data: RegionIn):
    region = await Region.create(**data.model_dump())
    return await RegionOut.from_tortoise_orm(region)
