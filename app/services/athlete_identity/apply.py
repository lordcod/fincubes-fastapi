from typing import Optional

from app.core.errors import APIError, ErrorCode
from app.models.athlete.athlete import Athlete
from app.models.review.review_decision import ReviewDecision
from app.models.review.review_item import ReviewItem
from app.models.review.review_session import ReviewSession
from app.schemas.athlete.review import (
    ReviewApplyDecisionItem,
    ReviewApplyResultItem,
    SuggestedPatch,
)
from app.schemas.results.result import BulkCreateResult
from app.services.athlete_identity.normalizer import is_empty_value, is_meaningful_value, is_weak_value
from app.shared.enums.enums import ReviewDecisionActionEnum, ReviewItemStatusEnum, ReviewSessionStatusEnum

RESOLVED_ITEM_STATUSES = {
    ReviewItemStatusEnum.MATCHED_EXISTING,
    ReviewItemStatusEnum.ENRICH_PENDING,
    ReviewItemStatusEnum.CREATED_NEW,
    ReviewItemStatusEnum.DONE,
}
RESOLVED_ITEM_STATUS_VALUES = tuple(RESOLVED_ITEM_STATUSES)
REVIEW_ACTION_NAME_BY_ENUM = {
    ReviewDecisionActionEnum.MATCH_EXISTING: "match_existing",
    ReviewDecisionActionEnum.ENRICH_EXISTING: "enrich_existing",
    ReviewDecisionActionEnum.CREATE_NEW: "create_new",
    ReviewDecisionActionEnum.MANUAL: "manual_review",
    ReviewDecisionActionEnum.SKIP: "manual_review",
}


def safe_patch_payload(source_patch: Optional[dict], athlete: Athlete) -> dict:
    if not source_patch:
        return {}

    safe: dict = {}
    for field in ("city", "license"):
        value = source_patch.get(field)
        if not is_empty_value(value) and is_empty_value(getattr(athlete, field)):
            safe[field] = value

    club_value = source_patch.get("club")
    if not is_empty_value(club_value) and is_meaningful_value(club_value):
        athlete_club = getattr(athlete, "club")
        if is_empty_value(athlete_club) or is_weak_value(athlete_club):
            safe["club"] = club_value
    return safe


def normalize_review_action_name(action: ReviewDecisionActionEnum | str) -> str:
    if isinstance(action, ReviewDecisionActionEnum):
        return REVIEW_ACTION_NAME_BY_ENUM[action]
    if action == "manual":
        return "manual_review"
    if action == "match":
        return "match_existing"
    return action


def is_review_item_resolved(status: ReviewItemStatusEnum) -> bool:
    return status in RESOLVED_ITEM_STATUSES


def review_item_action_from_status(item: ReviewItem) -> str:
    if item.status == ReviewItemStatusEnum.MATCHED_EXISTING:
        return "match_existing"
    if item.status in {ReviewItemStatusEnum.ENRICH_PENDING, ReviewItemStatusEnum.DONE}:
        return "enrich_existing"
    if item.status == ReviewItemStatusEnum.CREATED_NEW:
        return "create_new"
    if item.status == ReviewItemStatusEnum.AUTO_MATCH_CANDIDATE and item.selected_athlete_id is not None:
        for candidate in item.candidates_snapshot or []:
            if candidate.get("athlete_id") == item.selected_athlete_id and candidate.get("suggested_patch"):
                return "enrich_existing"
        return "match_existing"
    return "manual_review"


def _reasons_from_note(note: Optional[str]) -> list[str]:
    if not note:
        return []
    return [part.strip() for part in note.split(";") if part.strip()]


def _candidate_snapshot_for(item: ReviewItem, athlete_id: Optional[int]) -> Optional[dict]:
    if athlete_id is None:
        return None
    for candidate in item.candidates_snapshot or []:
        if candidate.get("athlete_id") == athlete_id or candidate.get("id") == athlete_id:
            return candidate
    return None


def get_review_item_context(
    item: ReviewItem,
    *,
    action_name: Optional[str] = None,
    athlete_id: Optional[int] = None,
    updated_fields: Optional[list[str]] = None,
) -> tuple[list[str], list[str], list[str]]:
    chosen_action = action_name or review_item_action_from_status(item)
    snapshot = _candidate_snapshot_for(item, athlete_id or item.selected_athlete_id)

    reasons = list(snapshot.get("reasons", [])) if snapshot else _reasons_from_note(item.note)
    conflicts = list(snapshot.get("conflicts", [])) if snapshot else []

    if not reasons:
        if chosen_action == "create_new":
            reasons = ["new athlete created from review decision"]
        elif chosen_action == "manual_review":
            reasons = ["item remains unresolved and requires manual review"]
        elif chosen_action == "enrich_existing":
            reasons = ["existing athlete safely enriched from review decision"]
        elif chosen_action == "match_existing":
            reasons = ["existing athlete selected from review decision"]

    return reasons, conflicts, list(updated_fields or [])


async def apply_safe_enrich(athlete: Athlete, patch: SuggestedPatch | dict | None) -> list[str]:
    if patch is None:
        return []
    patch_payload = patch if isinstance(patch, dict) else patch.model_dump(exclude_none=True)
    changes = safe_patch_payload(patch_payload, athlete)
    if not changes:
        return []
    athlete.update_from_dict(changes)
    await athlete.save(update_fields=[*changes.keys(), "updated_at"])
    return sorted(changes.keys())


async def apply_review_decision(item: ReviewItem, decision: ReviewApplyDecisionItem) -> ReviewApplyResultItem:
    updated_fields: list[str] = []
    created_athlete = None
    candidate_athlete = None

    if decision.action in {
        ReviewDecisionActionEnum.MATCH_EXISTING,
        ReviewDecisionActionEnum.ENRICH_EXISTING,
    }:
        if decision.athlete_id is None:
            raise APIError(ErrorCode.ATHLETE_NOT_FOUND)
        candidate_athlete = await Athlete.get_or_none(id=decision.athlete_id)
        if candidate_athlete is None:
            raise APIError(ErrorCode.ATHLETE_NOT_FOUND)

        if decision.action == ReviewDecisionActionEnum.ENRICH_EXISTING:
            updated_fields = await apply_safe_enrich(candidate_athlete, decision.patch)
            item.status = ReviewItemStatusEnum.ENRICH_PENDING
        else:
            item.status = ReviewItemStatusEnum.MATCHED_EXISTING
        item.selected_athlete_id = candidate_athlete.id

    elif decision.action == ReviewDecisionActionEnum.CREATE_NEW:
        source = item.source_payload
        created_athlete = await Athlete.create(
            last_name=source["last_name"],
            first_name=source["first_name"],
            birth_year=str(source["birth_year"]),
            gender=(source.get("gender") or "").upper(),
            city=source.get("city"),
            club=source.get("team"),
            license=source.get("rank"),
        )
        item.selected_athlete_id = created_athlete.id
        item.status = ReviewItemStatusEnum.CREATED_NEW

    elif decision.action == ReviewDecisionActionEnum.SKIP:
        item.status = ReviewItemStatusEnum.SKIPPED
        item.selected_athlete_id = None

    elif decision.action == ReviewDecisionActionEnum.MANUAL:
        item.status = ReviewItemStatusEnum.NEEDS_MANUAL_REVIEW
        item.selected_athlete_id = None
        item.note = decision.note or item.note

    await item.save()

    action_name = normalize_review_action_name(decision.action)
    reasons, conflicts, updated_fields = get_review_item_context(
        item,
        action_name=action_name,
        athlete_id=item.selected_athlete_id,
        updated_fields=updated_fields,
    )
    resolved = is_review_item_resolved(item.status)

    await ReviewDecision.create(
        review_item=item,
        action=decision.action,
        candidate_athlete=candidate_athlete,
        patch_payload=decision.patch,
        created_athlete=created_athlete,
        result_payload={
            "action": action_name,
            "resolved": resolved,
            "reasons": reasons,
            "conflicts": conflicts,
            "updated_fields": updated_fields,
            "selected_athlete_id": item.selected_athlete_id,
        },
    )

    return ReviewApplyResultItem(
        review_item_id=item.id,
        external_id=item.external_id,
        action=action_name,
        status=item.status,
        resolved=resolved,
        athlete_id=item.selected_athlete_id,
        selected_athlete_id=item.selected_athlete_id,
        created_athlete_id=created_athlete.id if created_athlete else None,
        reasons=reasons,
        conflicts=conflicts,
        updated_fields=updated_fields,
    )


async def maybe_complete_session(session: ReviewSession) -> None:
    remaining = await ReviewItem.filter(session=session).exclude(
        status__in=(*RESOLVED_ITEM_STATUS_VALUES, ReviewItemStatusEnum.SKIPPED)
    ).count()
    if remaining == 0:
        session.status = ReviewSessionStatusEnum.COMPLETED
        await session.save(update_fields=["status", "updated_at"])


async def validate_result_upload_resolution(
    results_data: list[BulkCreateResult],
    resolution_session_id: Optional[int],
) -> None:
    if resolution_session_id is None:
        raise APIError(ErrorCode.REVIEW_SESSION_NOT_FOUND)

    session = await ReviewSession.get_or_none(id=resolution_session_id)
    if session is None or session.status != ReviewSessionStatusEnum.COMPLETED:
        raise APIError(ErrorCode.REVIEW_SESSION_NOT_FOUND)

    required_external_ids: list[str] = []
    external_to_athlete_id: dict[str, int] = {}
    for result_item in results_data:
        if is_empty_value(result_item.external_id):
            raise APIError(ErrorCode.REVIEW_ITEM_NOT_FOUND)

        external_id = result_item.external_id.strip()
        required_external_ids.append(external_id)
        expected_athlete_id = external_to_athlete_id.get(external_id)
        if expected_athlete_id is not None and expected_athlete_id != result_item.athlete_id:
            raise APIError(ErrorCode.REVIEW_ITEM_NOT_FOUND)
        external_to_athlete_id[external_id] = result_item.athlete_id

    resolved_rows = await ReviewItem.filter(
        session_id=resolution_session_id,
        external_id__in=required_external_ids,
        status__in=RESOLVED_ITEM_STATUS_VALUES,
    ).values("external_id", "selected_athlete_id", "status")
    resolved_by_external_id = {
        row["external_id"]: row["selected_athlete_id"]
        for row in resolved_rows
        if row["selected_athlete_id"] is not None
    }

    for external_id, athlete_id in external_to_athlete_id.items():
        resolved_athlete_id = resolved_by_external_id.get(external_id)
        if resolved_athlete_id is None or resolved_athlete_id != athlete_id:
            raise APIError(ErrorCode.REVIEW_ITEM_NOT_FOUND)
