from dataclasses import dataclass, field
from typing import Optional

from app.schemas.athlete.review import ResolveCandidateItem, SuggestedPatch
from app.services.athlete_identity.scorer import confidence_from_signals
from app.shared.enums.enums import ReviewConfidenceEnum, ReviewDecisionActionEnum


@dataclass
class IdentityDecision:
    action: ReviewDecisionActionEnum
    confidence: ReviewConfidenceEnum
    athlete_id: Optional[int] = None
    suggested_patch: Optional[SuggestedPatch] = None
    reasons: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)


def _is_safe_match(candidate: ResolveCandidateItem) -> bool:
    signals = candidate.signals
    return (
        signals["identity_fields_match"]
        and not signals["city_conflict"]
        and not signals["club_conflict"]
        and (
            signals["city_match"]
            or signals["city_missing"]
            or signals["existing_more_specific"]
            or signals["source_more_specific"]
        )
        and (
            signals["club_exact_match"]
            or signals["club_compatible"]
            or signals["club_missing"]
            or signals["source_more_specific"]
            or signals["existing_more_specific"]
        )
    )


def _is_strict_high_confidence(candidate: ResolveCandidateItem, candidate_count: int) -> bool:
    signals = candidate.signals
    return (
        candidate_count == 1
        and signals["identity_fields_match"]
        and signals["city_match"]
        and not signals["city_conflict"]
        and not signals["club_conflict"]
        and (signals["club_exact_match"] or signals["club_compatible"])
        and not signals["source_more_specific"]
        and not signals["existing_more_specific"]
    )


def _has_meaningful_conflict(candidate: ResolveCandidateItem) -> bool:
    signals = candidate.signals
    return bool(signals["club_conflict_meaningful"] or signals["city_conflict_meaningful"])


def decide_identity(candidates: list[ResolveCandidateItem]) -> IdentityDecision:
    if not candidates:
        return IdentityDecision(
            action=ReviewDecisionActionEnum.CREATE_NEW,
            confidence=ReviewConfidenceEnum.LOW,
            reasons=["no existing candidate found"],
        )

    sorted_candidates = sorted(candidates, key=lambda candidate: (-candidate.score, candidate.id))
    best = sorted_candidates[0]
    candidate_count = len(sorted_candidates)
    best_confidence = confidence_from_signals(
        best.signals,
        candidate_count=candidate_count,
        has_suggested_patch=best.suggested_patch is not None,
    )

    if candidate_count > 1:
        return IdentityDecision(
            action=ReviewDecisionActionEnum.MANUAL,
            confidence=ReviewConfidenceEnum.LOW,
            athlete_id=best.id,
            suggested_patch=best.suggested_patch,
            reasons=["multiple candidates require manual review"],
            conflicts=["ambiguous candidates"],
        )

    if _has_meaningful_conflict(best):
        return IdentityDecision(
            action=ReviewDecisionActionEnum.CREATE_NEW,
            confidence=ReviewConfidenceEnum.LOW,
            reasons=["meaningful city/club conflict requires a new athlete"],
            conflicts=best.conflicts,
        )

    if best.suggested_patch is not None and _is_safe_match(best):
        return IdentityDecision(
            action=ReviewDecisionActionEnum.ENRICH_EXISTING,
            confidence=ReviewConfidenceEnum.MEDIUM,
            athlete_id=best.id,
            suggested_patch=best.suggested_patch,
            reasons=["safe enrich is possible without city or club conflicts"],
        )

    if _is_strict_high_confidence(best, candidate_count):
        return IdentityDecision(
            action=ReviewDecisionActionEnum.MATCH_EXISTING,
            confidence=ReviewConfidenceEnum.HIGH,
            athlete_id=best.id,
            reasons=["single candidate with matching city and compatible club context"],
        )

    if _is_safe_match(best):
        return IdentityDecision(
            action=ReviewDecisionActionEnum.MANUAL,
            confidence=best_confidence,
            athlete_id=best.id,
            suggested_patch=best.suggested_patch,
            reasons=["candidate is viable but not strict enough for automatic resolution"],
        )

    return IdentityDecision(
        action=ReviewDecisionActionEnum.MANUAL,
        confidence=ReviewConfidenceEnum.LOW,
        athlete_id=best.id,
        suggested_patch=best.suggested_patch,
        reasons=["mixed or incomplete signals require manual review"],
        conflicts=best.conflicts,
    )
