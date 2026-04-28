from fastapi import APIRouter

from app.core.errors import APIError, ErrorCode
from app.models.review.review_item import ReviewItem
from app.models.review.review_session import ReviewSession
from app.schemas.athlete.review import (
    ResolveCandidatesRequest,
    ReviewSessionItemResponse,
    ReviewSessionItemsListResponse,
    ReviewSessionLoadItemsResponse,
)
from app.services.athlete_identity import resolve_source_candidates
from app.services.athlete_identity.apply import (
    get_review_item_context,
    is_review_item_resolved,
    review_item_action_from_status,
)
from app.shared.enums.enums import ReviewItemStatusEnum, ReviewSessionStatusEnum
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


def serialize_review_item(item: ReviewItem) -> ReviewSessionItemResponse:
    latest_decision = None
    decisions = getattr(item, "decisions", None)
    if decisions:
        latest_decision = max(decisions, key=lambda decision: decision.id)
    result_payload = latest_decision.result_payload if latest_decision and latest_decision.result_payload else {}
    action = result_payload.get("action") or review_item_action_from_status(item)
    resolved = result_payload.get("resolved")
    if resolved is None:
        resolved = is_review_item_resolved(item.status)
    reasons, conflicts, updated_fields = get_review_item_context(
        item,
        action_name=action,
        athlete_id=result_payload.get("selected_athlete_id") or item.selected_athlete_id,
        updated_fields=result_payload.get("updated_fields", []),
    )
    reasons = result_payload.get("reasons", reasons)
    conflicts = result_payload.get("conflicts", conflicts)
    return ReviewSessionItemResponse(
        id=item.id,
        external_id=item.external_id,
        status=item.status,
        action=action,
        auto_match=item.auto_match,
        confidence=item.confidence,
        source_payload=item.source_payload,
        selected_athlete_id=item.selected_athlete_id,
        resolved=resolved,
        reasons=reasons,
        conflicts=conflicts,
        updated_fields=updated_fields,
        candidates_snapshot=item.candidates_snapshot or [],
        note=item.note,
        created_at=item.created_at.isoformat() if item.created_at else None,
        updated_at=item.updated_at.isoformat() if item.updated_at else None,
    )


@router.post("/", response_model=ReviewSessionLoadItemsResponse)
@require_scope("athlete:write")
async def load_review_session_items(id: int, payload: ResolveCandidatesRequest):
    session = await ReviewSession.get_or_none(id=id)
    if session is None:
        raise APIError(ErrorCode.REVIEW_SESSION_NOT_FOUND)

    created = 0
    updated = 0
    for source in payload.items:
        resolution = await resolve_source_candidates(source)
        status = (
            ReviewItemStatusEnum.AUTO_MATCH_CANDIDATE
            if resolution.auto_match
            else ReviewItemStatusEnum.NEEDS_MANUAL_REVIEW
        )
        candidates_snapshot = [
            candidate.model_dump(mode="json") for candidate in resolution.candidates
        ]
        item = await ReviewItem.get_or_none(session_id=id, external_id=source.external_id)
        payload_data = source.model_dump(mode="json")
        selected_athlete_id = resolution.decision.athlete_id if resolution.auto_match else None

        if item is None:
            await ReviewItem.create(
                session=session,
                external_id=source.external_id,
                status=status,
                source_payload=payload_data,
                source_city=source.city,
                candidates_snapshot=candidates_snapshot,
                candidate_count=len(candidates_snapshot),
                selected_athlete_id=selected_athlete_id,
                auto_match=resolution.auto_match,
                confidence=resolution.decision.confidence,
                note="; ".join(resolution.decision.reasons) or None,
            )
            created += 1
        else:
            item.status = status
            item.source_payload = payload_data
            item.source_city = source.city
            item.candidates_snapshot = candidates_snapshot
            item.candidate_count = len(candidates_snapshot)
            item.selected_athlete_id = selected_athlete_id
            item.auto_match = resolution.auto_match
            item.confidence = resolution.decision.confidence
            item.note = "; ".join(resolution.decision.reasons) or item.note
            await item.save()
            updated += 1

    if session.status == ReviewSessionStatusEnum.NEW:
        session.status = ReviewSessionStatusEnum.ACTIVE
        await session.save(update_fields=["status", "updated_at"])

    return ReviewSessionLoadItemsResponse(created=created, updated=updated)


@router.get("/", response_model=ReviewSessionItemsListResponse)
@require_scope("athlete:read")
async def list_review_session_items(id: int):
    session = await ReviewSession.get_or_none(id=id)
    if session is None:
        raise APIError(ErrorCode.REVIEW_SESSION_NOT_FOUND)

    items = await ReviewItem.filter(session_id=id).prefetch_related("decisions").order_by("id")
    return ReviewSessionItemsListResponse(
        total=len(items),
        items=[serialize_review_item(item) for item in items],
    )
