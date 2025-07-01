

from typing import List, Optional

from fastapi import APIRouter, Depends

from app.core.security.permissions import admin_required
from app.models.misc.standard_category import StandardCategory
from app.schemas.results.standards import StandardIn, StandardOut

router = APIRouter(tags=['Admin/Standard'])


@router.post("/", dependencies=[Depends(admin_required)], response_model=StandardOut)
async def create_standard(data: StandardIn):
    await StandardCategory.filter(
        code=data.code,
        stroke=data.stroke,
        distance=data.distance,
        gender=data.gender,
        type=data.type,
        is_active=True,
    ).update(is_active=False)

    standard = await StandardCategory.create(**data.model_dump())
    return await StandardOut.from_tortoise_orm(standard)
