from fastapi import APIRouter, Depends

from app.schemas.athlete.review import (
    ResolveCandidatesRequest,
    ResolveCandidatesResponse,
    ResolveCandidatesResponseItem,
)
from app.services.athlete_identity import resolve_source_candidates, source_cache_key
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.post(
    "/",
    response_model=ResolveCandidatesResponse,
)
@require_scope("athlete:read")
async def resolve_candidates(payload: ResolveCandidatesRequest):
    cache = {}
    response_items: list[ResolveCandidatesResponseItem] = []

    for item in payload.items:
        key = source_cache_key(item)
        cached = cache.get(key)
        if cached is None:
            cached = await resolve_source_candidates(item)
            cache[key] = cached

        response_items.append(
            ResolveCandidatesResponseItem(
                external_id=item.external_id,
                candidates=cached.candidates,
                auto_match=cached.auto_match,
                confidence=cached.decision.confidence,
                recommended_action=cached.recommended_action,
                recommended_athlete_id=cached.decision.athlete_id,
                reasons=cached.decision.reasons,
                conflicts=cached.decision.conflicts,
            )
        )

    return ResolveCandidatesResponse(items=response_items)
