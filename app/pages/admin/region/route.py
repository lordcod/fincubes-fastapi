
from typing import List

from fastapi import APIRouter
from app.models.misc.region import Region
from app.schemas.region.region import RegionIn, RegionOut
from app.shared.clients.scopes.request import require_scope

router = APIRouter(tags=['Admin/Region'])


@router.post("/", response_model=RegionOut)
@require_scope('region:create')
async def create_region(data: RegionIn):
    region = await Region.create(**data.model_dump())
    return await RegionOut.from_tortoise_orm(region)
