from fastapi import APIRouter, Depends

from app.schemas.athlete.review import ResolvePreviewRequest, ResolvePreviewResponse
from app.services.athlete_identity import build_preview
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.post(
    "/",
    response_model=ResolvePreviewResponse,
)
@require_scope("athlete:read")
async def resolve_preview(payload: ResolvePreviewRequest):
    return await build_preview(payload)
