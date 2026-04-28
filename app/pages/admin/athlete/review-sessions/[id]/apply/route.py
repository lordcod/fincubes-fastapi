from fastapi import APIRouter

from app.core.errors import APIError, ErrorCode
from app.models.review.review_item import ReviewItem
from app.models.review.review_session import ReviewSession
from app.schemas.athlete.review import (
    ReviewApplyErrorItem,
    ReviewApplyRequest,
    ReviewApplyResponse,
    ReviewApplyResultItem,
)
from app.services.athlete_identity.apply import (
    apply_review_decision,
    maybe_complete_session,
)
from app.shared.enums.enums import ReviewDecisionActionEnum
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.post("/", response_model=ReviewApplyResponse)
@require_scope("athlete:write")
async def apply_review_decisions(id: int, payload: ReviewApplyRequest):
    session = await ReviewSession.get_or_none(id=id)
    if session is None:
        raise APIError(ErrorCode.REVIEW_SESSION_NOT_FOUND)

    response = ReviewApplyResponse()
    items_by_id = {
        item.id: item
        for item in await ReviewItem.filter(
            id__in=[decision.review_item_id for decision in payload.items],
            session_id=id,
        )
    }

    for decision in payload.items:
        item = items_by_id.get(decision.review_item_id)
        if item is None:
            response.errors.append(
                ReviewApplyErrorItem(
                    review_item_id=decision.review_item_id,
                    action=decision.action,
                    error=ErrorCode.REVIEW_ITEM_NOT_FOUND.name,
                )
            )
            continue

        try:
            response.items.append(await apply_review_decision(item, decision))
        except Exception as exc:
            response.errors.append(
                ReviewApplyErrorItem(
                    review_item_id=decision.review_item_id,
                    action=decision.action,
                    error=str(exc),
                )
            )

    await maybe_complete_session(session)
    return response
