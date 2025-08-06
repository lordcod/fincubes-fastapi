from fastapi import APIRouter
from app.models.misc.standard_category import StandardCategory
from app.schemas.results.standards import StandardIn, StandardOut
from app.shared.clients.scopes.request import require_scope

router = APIRouter(tags=['Admin/Standard'])


@router.post("/", response_model=StandardOut)
@require_scope('standard:create')
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
