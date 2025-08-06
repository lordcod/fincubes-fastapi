

from typing import List, Optional

from fastapi import APIRouter, Depends


from app.models.misc.standard_category import StandardCategory
from app.schemas.results.standards import StandardIn, StandardOut
from app.shared.clients.scopes.request import require_scope

router = APIRouter(tags=['Public/Server/Standards'])


@router.get("/", response_model=List[StandardOut])
@require_scope('standard:read')
async def list_standards(
    stroke: Optional[str] = None,
    distance: Optional[int] = None,
    gender: Optional[str] = None,
    type: Optional[str] = None,
    code: Optional[str] = None,
):
    filters = {"is_active": True}
    if stroke:
        filters["stroke"] = stroke
    if distance:
        filters["distance"] = distance
    if gender:
        filters["gender"] = gender
    if type:
        filters["type"] = type
    if code:
        filters["code"] = code

    query = StandardCategory.filter(**filters)
    return await StandardOut.from_queryset(query)
