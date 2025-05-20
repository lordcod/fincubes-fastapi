from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from models.models import StandardCategory
from schemas.standards import StandardIn, StandardOut
from misc.security import admin_required

router = APIRouter(prefix='/standard', tags=["standards"])


@router.post("/", dependencies=[Depends(admin_required)], response_model=StandardOut)
async def create_standard(data: StandardIn):
    await StandardCategory.filter(
        code=data.code,
        stroke=data.stroke,
        distance=data.distance,
        gender=data.gender,
        type=data.type,
        is_active=True
    ).update(is_active=False)

    standard = await StandardCategory.create(**data.model_dump())
    return standard


@router.get("/", response_model=List[StandardOut])
async def list_standards(
    stroke: Optional[str] = None,
    distance: Optional[int] = None,
    gender: Optional[str] = None,
    type: Optional[str] = None,
    code: Optional[str] = None
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

    return await StandardCategory.filter(**filters).all()


@router.get("/{standard_id}", response_model=StandardOut)
async def get_standard(standard_id: int):
    standard = await StandardCategory.filter(id=standard_id).first()
    if not standard:
        raise HTTPException(status_code=404, detail="Standard not found")
    return standard
