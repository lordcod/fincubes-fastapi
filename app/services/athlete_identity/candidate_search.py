from dataclasses import dataclass

from app.models.athlete.athlete import Athlete
from app.schemas.athlete.review import (
    ResolveCandidateItem,
    ResolveCandidateSourceItem,
    ResolveRecommendedAction,
)
from app.services.athlete_identity.decision_engine import IdentityDecision, decide_identity
from app.services.athlete_identity.normalizer import normalize_gender
from app.services.athlete_identity.scorer import is_same_candidate, to_candidate_response
from app.shared.enums.enums import ReviewDecisionActionEnum


@dataclass
class CandidateResolution:
    source: ResolveCandidateSourceItem
    candidates: list[ResolveCandidateItem]
    decision: IdentityDecision

    @property
    def recommended_action(self) -> ResolveRecommendedAction:
        if self.decision.action == ReviewDecisionActionEnum.MANUAL:
            return "manual_review"
        return self.decision.action.value

    @property
    def auto_match(self) -> bool:
        return self.decision.action in {
            ReviewDecisionActionEnum.MATCH_EXISTING,
            ReviewDecisionActionEnum.ENRICH_EXISTING,
        }


async def resolve_source_candidates(source: ResolveCandidateSourceItem) -> CandidateResolution:
    base_query = Athlete.filter(
        last_name__iexact=source.last_name.strip(),
        first_name__iexact=source.first_name.strip(),
        birth_year=str(source.birth_year),
    )
    gender = normalize_gender(source.gender)
    if gender:
        base_query = base_query.filter(gender=gender)

    athletes = await base_query.limit(50)

    candidates: list[ResolveCandidateItem] = []
    for athlete in athletes:
        if not is_same_candidate(source, athlete):
            continue
        candidate, _ = to_candidate_response(source, athlete)
        candidates.append(candidate)

    candidates.sort(key=lambda candidate: (-candidate.score, candidate.id))
    return CandidateResolution(
        source=source,
        candidates=candidates,
        decision=decide_identity(candidates),
    )
