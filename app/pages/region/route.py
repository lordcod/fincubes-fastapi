
from typing import List

from fastapi import APIRouter, Depends

from app.core.security.permissions import admin_required
from app.models.misc.region import Region
from app.schemas.region.region import RegionIn, RegionOut

router = APIRouter()


@router.post("/", dependencies=[Depends(admin_required)], response_model=RegionOut)
async def create_region(data: RegionIn):
    region = await Region.create(**data.model_dump())
    return await RegionOut.from_tortoise_orm(region)


@router.get("/", response_model=List[RegionOut])
async def list_regions():
    query = Region.all()
    return await RegionOut.from_queryset(query)
