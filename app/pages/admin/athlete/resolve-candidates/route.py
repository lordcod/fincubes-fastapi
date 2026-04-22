from fastapi import APIRouter, Depends

from app.models.athlete.athlete import Athlete
from app.schemas.athlete.review import (
    ResolveCandidatesRequest,
    ResolveCandidatesResponse,
    ResolveCandidatesResponseItem,
)
from app.shared.utils.athlete_identity import (
    AUTO_MATCH_THRESHOLD,
    is_same_candidate,
    source_cache_key,
    to_candidate_response,
)
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.post(
    "/",
    response_model=ResolveCandidatesResponse,
)
@require_scope("athlete:read")
async def resolve_candidates(payload: ResolveCandidatesRequest):
    cache: dict[tuple[str, ...], tuple[list, bool]] = {}
    response_items: list[ResolveCandidatesResponseItem] = []

    for item in payload.items:
        key = source_cache_key(item)
        cached = cache.get(key)
        if cached is None:
            base_query = Athlete.filter(
                last_name__iexact=item.last_name.strip(),
                first_name__iexact=item.first_name.strip(),
                birth_year=str(item.birth_year),
            )
            if item.gender:
                base_query = base_query.filter(gender=item.gender.strip().upper())

            athletes = await base_query.limit(50)

            candidates = []
            has_conflict = False
            for athlete in athletes:
                if not is_same_candidate(item, athlete):
                    continue
                candidate, candidate_conflict = to_candidate_response(item, athlete)
                candidates.append(candidate)
                has_conflict = has_conflict or candidate_conflict

            candidates.sort(key=lambda candidate: (-candidate.score, candidate.id))
            auto_match = (
                len(candidates) == 1
                and candidates[0].score >= AUTO_MATCH_THRESHOLD
                and not has_conflict
            )
            cached = (candidates, auto_match)
            cache[key] = cached

        candidates, auto_match = cached
        response_items.append(
            ResolveCandidatesResponseItem(
                external_id=item.external_id,
                candidates=candidates,
                auto_match=auto_match,
            )
        )

    return ResolveCandidatesResponse(items=response_items)
