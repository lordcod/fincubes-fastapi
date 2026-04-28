from dataclasses import dataclass, field
from typing import Optional

from app.models.athlete.athlete import Athlete
from app.schemas.athlete.review import (
    ResolveCandidateItem,
    ResolveCandidateSourceItem,
    SuggestedPatch,
)
from app.services.athlete_identity.normalizer import (
    TEAM_KIND_GENERIC,
    TEAM_KIND_REGION,
    classify_team_kind,
    is_empty_value,
    is_meaningful_value,
    is_weak_value,
    normalize_gender,
    normalize_text,
    tokenize,
)
from app.shared.enums.enums import ReviewConfidenceEnum

AUTO_MATCH_THRESHOLD = 220
MEDIUM_CONFIDENCE_THRESHOLD = 120
CLUB_NOISE_TOKENS = {
    "мау",
    "мбу",
    "гбу",
    "до",
    "дюсш",
    "сдюсшор",
    "сш",
    "сшор",
    "ксшор",
    "ск",
    "клуб",
    "спортивная",
    "школа",
    "им",
    "имени",
}


@dataclass
class ScoreResult:
    score: int
    reasons: list[str]
    conflicts: list[str] = field(default_factory=list)
    signals: dict[str, object] = field(default_factory=dict)

    @property
    def has_conflict(self) -> bool:
        return bool(self.conflicts)


def _informative_tokens(value: Optional[str]) -> set[str]:
    return {token for token in tokenize(value) if token not in CLUB_NOISE_TOKENS}


def _can_enrich_club(existing_value: Optional[str], source_value: Optional[str]) -> bool:
    if is_empty_value(source_value) or not is_meaningful_value(source_value):
        return False
    return is_empty_value(existing_value) or is_weak_value(existing_value)


def _can_enrich_city(existing_value: Optional[str], source_value: Optional[str]) -> bool:
    return not is_empty_value(source_value) and is_empty_value(existing_value)


def _can_enrich_license(existing_value: Optional[str], source_value: Optional[str]) -> bool:
    return not is_empty_value(source_value) and is_empty_value(existing_value)


def confidence_from_signals(
    signals: dict[str, object],
    *,
    candidate_count: Optional[int] = None,
    has_suggested_patch: bool = False,
) -> ReviewConfidenceEnum:
    if signals["city_conflict"] or signals["club_conflict"]:
        return ReviewConfidenceEnum.LOW

    strict_match = (
        signals["identity_fields_match"]
        and signals["city_match"]
        and (signals["club_exact_match"] or signals["club_compatible"])
        and not signals["source_more_specific"]
        and not signals["existing_more_specific"]
    )
    if candidate_count == 1 and strict_match:
        return ReviewConfidenceEnum.HIGH

    if signals["identity_fields_match"] and not signals["city_conflict"] and not signals["club_conflict"]:
        if has_suggested_patch or signals["city_missing"] or signals["club_missing"]:
            return ReviewConfidenceEnum.MEDIUM
        if strict_match:
            return ReviewConfidenceEnum.MEDIUM

    return ReviewConfidenceEnum.LOW


def confidence_from_score(score: int, has_conflict: bool = False) -> ReviewConfidenceEnum:
    if has_conflict:
        return ReviewConfidenceEnum.LOW
    if score >= AUTO_MATCH_THRESHOLD:
        return ReviewConfidenceEnum.HIGH
    if score >= MEDIUM_CONFIDENCE_THRESHOLD:
        return ReviewConfidenceEnum.MEDIUM
    return ReviewConfidenceEnum.LOW


def build_suggested_patch(source: ResolveCandidateSourceItem, athlete: Athlete) -> Optional[SuggestedPatch]:
    patch = SuggestedPatch()

    if _can_enrich_club(athlete.club, source.team):
        patch.club = source.team.strip()
    if _can_enrich_city(athlete.city, source.city):
        patch.city = source.city.strip()
    if _can_enrich_license(athlete.license, source.rank):
        patch.license = source.rank.strip()

    if not patch.model_dump(exclude_none=True):
        return None
    return patch


def score_candidate(source: ResolveCandidateSourceItem, athlete: Athlete) -> ScoreResult:
    source_city = normalize_text(source.city)
    athlete_city = normalize_text(athlete.city)
    source_team = normalize_text(source.team)
    athlete_club = normalize_text(athlete.club)
    source_team_kind = classify_team_kind(source.team)
    candidate_club_kind = classify_team_kind(athlete.club)
    source_team_meaningful = is_meaningful_value(source.team)
    candidate_club_meaningful = is_meaningful_value(athlete.club)
    existing_club_empty = is_empty_value(athlete.club)
    existing_club_weak = is_weak_value(athlete.club)

    signals: dict[str, object] = {
        "name_match": True,
        "birth_year_match": True,
        "gender_match": True,
        "identity_fields_match": True,
        "team_kind": source_team_kind,
        "candidate_club_kind": candidate_club_kind,
        "source_team_meaningful": source_team_meaningful,
        "candidate_club_meaningful": candidate_club_meaningful,
        "existing_club_empty": existing_club_empty,
        "existing_club_weak": existing_club_weak,
        "city_match": False,
        "city_conflict": False,
        "city_conflict_meaningful": False,
        "city_missing": is_empty_value(source.city) or is_empty_value(athlete.city),
        "club_exact_match": False,
        "club_compatible": False,
        "club_conflict": False,
        "club_conflict_meaningful": False,
        "club_missing": is_empty_value(source.team) or is_empty_value(athlete.club),
        "source_more_specific": False,
        "existing_more_specific": False,
        "safe_enrich_city": _can_enrich_city(athlete.city, source.city),
        "safe_enrich_club": _can_enrich_club(athlete.club, source.team),
        "safe_enrich_license": _can_enrich_license(athlete.license, source.rank),
    }

    reasons: list[str] = []
    conflicts: list[str] = []
    score = 0

    if signals["city_missing"]:
        reasons.append("city context is incomplete")
        score += 10
    elif source_city == athlete_city:
        signals["city_match"] = True
        reasons.append("same city")
        score += 120
    else:
        signals["city_conflict"] = True
        signals["city_conflict_meaningful"] = source_team_kind not in {TEAM_KIND_REGION, TEAM_KIND_GENERIC}
        conflicts.append("different city")
        reasons.append("different city")
        score -= 160 if signals["city_conflict_meaningful"] else 60

    if is_empty_value(source.team) and is_empty_value(athlete.club):
        reasons.append("club context is missing on both sides")
        score += 5
    elif is_empty_value(source.team):
        reasons.append("source team is missing")
        score += 10
    elif source_team == athlete_club:
        signals["club_exact_match"] = True
        signals["club_compatible"] = True
        reasons.append("same team/club")
        score += 180
    elif signals["safe_enrich_club"]:
        signals["source_more_specific"] = True
        signals["club_compatible"] = True
        reasons.append("source club is more specific than existing club")
        score += 90
    elif source_team_meaningful and not candidate_club_meaningful and not existing_club_empty:
        signals["source_more_specific"] = True
        signals["club_compatible"] = True
        reasons.append("source club is more specific than weak existing club")
        score += 70
    elif candidate_club_meaningful and is_weak_value(source.team):
        signals["existing_more_specific"] = True
        signals["club_compatible"] = True
        reasons.append("existing club is more specific than source team")
        score += 50
    else:
        source_tokens = _informative_tokens(source.team)
        candidate_tokens = _informative_tokens(athlete.club)
        if source_tokens and candidate_tokens and (
            source_tokens.issubset(candidate_tokens)
            or candidate_tokens.issubset(source_tokens)
            or bool(source_tokens & candidate_tokens)
        ):
            signals["club_compatible"] = True
            reasons.append("club contexts are compatible")
            score += 130
        elif not source_team_meaningful or not candidate_club_meaningful:
            reasons.append("club context is weak or generic")
            score += 20
        else:
            signals["club_conflict"] = True
            signals["club_conflict_meaningful"] = True
            conflicts.append("different meaningful clubs")
            reasons.append("different meaningful clubs")
            score -= 220

    if signals["safe_enrich_city"]:
        reasons.append("source city can safely enrich existing athlete")
        score += 20
    if signals["safe_enrich_club"]:
        reasons.append("source club can safely enrich existing athlete")
        score += 25
    if signals["safe_enrich_license"]:
        reasons.append("source rank can safely enrich existing athlete")
        score += 10

    return ScoreResult(score=score, reasons=reasons, conflicts=conflicts, signals=signals)


def is_same_candidate(source: ResolveCandidateSourceItem, athlete: Athlete) -> bool:
    if normalize_text(athlete.last_name) != normalize_text(source.last_name):
        return False
    if normalize_text(athlete.first_name) != normalize_text(source.first_name):
        return False
    if str(athlete.birth_year) != str(source.birth_year):
        return False

    source_gender = normalize_gender(source.gender)
    if source_gender and normalize_gender(athlete.gender) != source_gender:
        return False

    return True


def to_candidate_response(source: ResolveCandidateSourceItem, athlete: Athlete) -> tuple[ResolveCandidateItem, bool]:
    score_result = score_candidate(source, athlete)
    suggested_patch = build_suggested_patch(source, athlete)
    confidence = confidence_from_signals(
        score_result.signals,
        has_suggested_patch=suggested_patch is not None,
    )

    candidate = ResolveCandidateItem(
        id=athlete.id,
        athlete_id=athlete.id,
        last_name=athlete.last_name,
        first_name=athlete.first_name,
        birth_year=int(athlete.birth_year),
        gender=athlete.gender,
        city=athlete.city,
        club=athlete.club,
        license=athlete.license,
        score=score_result.score,
        confidence=confidence,
        reasons=score_result.reasons,
        conflicts=score_result.conflicts,
        suggested_patch=suggested_patch,
        signals=score_result.signals,
    )
    return candidate, score_result.has_conflict
