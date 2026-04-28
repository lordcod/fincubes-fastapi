from fastapi import APIRouter

from app.models.review.review_session import ReviewSession
from app.schemas.athlete.review import ReviewSessionCreateRequest, ReviewSessionCreateResponse
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.post("/", response_model=ReviewSessionCreateResponse)
@require_scope("athlete:write")
async def create_review_session(payload: ReviewSessionCreateRequest):
    session = await ReviewSession.create(
        source_type=payload.source_type,
        source_ref=payload.source_ref,
        meta=payload.meta,
    )
    return ReviewSessionCreateResponse(id=session.id, status=session.status)
