from typing import List, Optional

from fastapi import APIRouter, Query

from app.models.misc.region_icon import RegionIcon
from app.schemas.region.icon import RegionIconOut
from app.shared.utils.scopes.request import require_scope

router = APIRouter(tags=["Public/Server/Region"])


@router.get("/", response_model=List[RegionIconOut])
@require_scope("region:read")
async def list_region_icons(
    query: Optional[str] = Query(default=None, min_length=1),
    limit: int = Query(default=50, ge=1, le=200),
):
    qs = RegionIcon.all()
    if query:
        qs = qs.filter(name__icontains=query.strip())
    return await qs.order_by("name").limit(limit).values(
        "name",
        "format",
        "icon_url",
    )
