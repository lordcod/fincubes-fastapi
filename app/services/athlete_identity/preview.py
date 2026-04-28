from app.core.errors import APIError, ErrorCode
from app.models.athlete.athlete import Athlete
from app.schemas.athlete.review import (
    BulkAthleteCreateItem,
    ResolvePreviewCreateItem,
    ResolvePreviewDecision,
    ResolvePreviewEnrichItem,
    ResolvePreviewItem,
    ResolvePreviewRequest,
    ResolvePreviewResponse,
    ResolvePreviewSummary,
    SuggestedPatch,
)
from app.services.athlete_identity.apply import safe_patch_payload
from app.services.athlete_identity.decision_engine import decide_identity
from app.services.athlete_identity.normalizer import is_empty_value
from app.services.athlete_identity.scorer import to_candidate_response
from app.shared.enums.enums import ReviewConfidenceEnum, ReviewDecisionActionEnum

MATCH_ACTIONS = {"match", "match_existing"}
MANUAL_ACTIONS = {"manual", "manual_review"}


def normalize_preview_action(action: str) -> str:
    if action == "match":
        return "match_existing"
    if action == "manual":
        return "manual_review"
    return action


def can_build_create_payload(item: ResolvePreviewDecision) -> bool:
    if item.source is None:
        return False
    return (
        not is_empty_value(item.source.last_name)
        and not is_empty_value(item.source.first_name)
        and item.source.birth_year is not None
        and not is_empty_value(item.source.gender)
    )


def build_create_payload(item: ResolvePreviewDecision) -> BulkAthleteCreateItem:
    source = item.source
    assert source is not None
    return BulkAthleteCreateItem(
        external_id=item.external_id,
        last_name=source.last_name,
        first_name=source.first_name,
        birth_year=source.birth_year,
        gender=(source.gender or "").upper(),
        city=source.city,
        club=source.team,
        license=source.rank,
    )


def build_safe_update_payload(item: ResolvePreviewDecision, athlete: Athlete):
    if item.source is None:
        return {}, None

    candidate, _ = to_candidate_response(item.source, athlete)
    decision = decide_identity([candidate])
    patch_payload = (
        candidate.suggested_patch.model_dump(exclude_none=True)
        if candidate.suggested_patch is not None
        else {}
    )
    safe_payload = safe_patch_payload(patch_payload, athlete)
    return safe_payload, decision


async def build_preview(payload: ResolvePreviewRequest) -> ResolvePreviewResponse:
    summary = ResolvePreviewSummary()
    preview_items: list[ResolvePreviewItem] = []
    enrich_updates: list[ResolvePreviewEnrichItem] = []
    create_payloads: list[ResolvePreviewCreateItem] = []

    athlete_ids = [item.athlete_id for item in payload.items if item.athlete_id is not None]
    athletes = await Athlete.filter(id__in=athlete_ids).all() if athlete_ids else []
    athletes_by_id = {athlete.id: athlete for athlete in athletes}

    for item in payload.items:
        normalized_action = normalize_preview_action(item.action)
        resolved = False
        athlete_id = item.athlete_id
        confidence = ReviewConfidenceEnum.LOW
        reasons: list[str] = []
        conflicts: list[str] = []
        update_payload = None
        create_payload = None

        if normalized_action in MATCH_ACTIONS or normalized_action == "enrich_existing":
            if item.athlete_id is None:
                raise APIError(ErrorCode.ATHLETE_NOT_FOUND)

            athlete = athletes_by_id.get(item.athlete_id)
            if athlete is None:
                raise APIError(ErrorCode.ATHLETE_NOT_FOUND)

            safe_payload, decision = build_safe_update_payload(item, athlete)
            if decision is not None:
                reasons = decision.reasons
                conflicts = decision.conflicts
                confidence = decision.confidence

            if normalized_action == "enrich_existing":
                if (
                    decision is not None
                    and decision.action == ReviewDecisionActionEnum.ENRICH_EXISTING
                    and safe_payload
                    and not conflicts
                ):
                    resolved = True
                    summary.matched += 1
                    summary.enrich_updates += 1
                    update_payload = safe_payload
                    enrich_updates.append(
                        ResolvePreviewEnrichItem(
                            external_id=item.external_id,
                            athlete_id=athlete.id,
                            suggested_patch=SuggestedPatch(**safe_payload),
                        )
                    )
                else:
                    normalized_action = "manual_review"
                    summary.need_manual += 1
                    reasons = reasons or ["unsafe enrich request requires manual review"]
                    conflicts = conflicts or ["safe enrich payload is not available"]
            else:
                if decision is not None and decision.action in {
                    ReviewDecisionActionEnum.MATCH_EXISTING,
                    ReviewDecisionActionEnum.ENRICH_EXISTING,
                }:
                    resolved = True
                    summary.matched += 1
                else:
                    normalized_action = "manual_review"
                    summary.need_manual += 1
                    reasons = reasons or ["unsafe match request requires manual review"]
                if resolved and safe_payload:
                    summary.enrich_updates += 1
                    update_payload = safe_payload
                    enrich_updates.append(
                        ResolvePreviewEnrichItem(
                            external_id=item.external_id,
                            athlete_id=athlete.id,
                            suggested_patch=SuggestedPatch(**safe_payload),
                        )
                    )

        elif normalized_action == "create_new":
            if can_build_create_payload(item):
                create_payload = build_create_payload(item)
                resolved = True
                summary.create_new += 1
                create_payloads.append(
                    ResolvePreviewCreateItem(
                        external_id=item.external_id,
                        payload=create_payload,
                    )
                )
                confidence = ReviewConfidenceEnum.LOW
                reasons = ["source has enough identity data to create a new athlete"]
            else:
                normalized_action = "manual_review"
                summary.need_manual += 1
                reasons = ["insufficient identity data for safe athlete creation"]
                conflicts = ["create payload is incomplete"]
                confidence = ReviewConfidenceEnum.LOW

        elif normalized_action == "skip":
            summary.skipped += 1
            reasons = ["item skipped by user"]
            confidence = ReviewConfidenceEnum.LOW
        elif normalized_action in MANUAL_ACTIONS:
            summary.need_manual += 1
            reasons = ["manual review requested"]
            confidence = ReviewConfidenceEnum.LOW
        else:
            summary.need_manual += 1
            normalized_action = "manual_review"
            reasons = ["unknown action requires manual review"]
            confidence = ReviewConfidenceEnum.LOW

        preview_items.append(
            ResolvePreviewItem(
                external_id=item.external_id,
                action=normalized_action,
                athlete_id=athlete_id,
                confidence=confidence,
                reasons=reasons,
                conflicts=conflicts,
                resolved=resolved,
                update_payload=update_payload,
                create_payload=create_payload,
            )
        )

    return ResolvePreviewResponse(summary=summary, items=preview_items, enrich_updates=enrich_updates, create_payloads=create_payloads)
