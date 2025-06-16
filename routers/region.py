from typing import List

from fastapi import APIRouter, Depends

from misc.errors import APIError, ErrorCode
from misc.security import admin_required
from models.models import Region
from schemas.region import RegionIn, RegionOut

router = APIRouter(prefix="/region", tags=["region"])


@router.post("/", dependencies=[Depends(admin_required)], response_model=RegionOut)
async def create_region(data: RegionIn):
    region = await Region.create(**data.model_dump())
    return await RegionOut.from_tortoise_orm(region)


@router.get("/", response_model=List[RegionOut])
async def list_regions():
    query = Region.all()
    return await RegionOut.from_queryset(query)


@router.get("/{id}", response_model=RegionOut)
async def get_region(id: int):
    standard = await Region.get(id=id)
    if not standard:
        raise APIError(ErrorCode.STANDARD_NOT_FOUND, status_code=404)
    return await RegionOut.from_tortoise_orm(standard)
