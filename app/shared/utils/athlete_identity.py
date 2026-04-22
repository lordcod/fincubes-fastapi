import re
from dataclasses import dataclass
from typing import Optional

from app.models.athlete.athlete import Athlete
from app.schemas.athlete.review import (
    ResolveCandidateItem,
    ResolveCandidateSourceItem,
    SuggestedPatch,
)

TOKEN_RE = re.compile(r"[0-9A-Za-zА-Яа-яЁё]+")
AUTO_MATCH_THRESHOLD = 220


def normalize_text(value: Optional[str]) -> str:
    if not value:
        return ""
    value = value.strip().lower().replace("ё", "е")
    value = value.replace('"', " ").replace("«", " ").replace("»", " ")
    value = re.sub(r"\s+", " ", value)
    return value


def tokenize(value: Optional[str]) -> set[str]:
    normalized = normalize_text(value)
    return {match.group(0) for match in TOKEN_RE.finditer(normalized)}


def normalize_gender(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    return value.strip().upper()


@dataclass
class ScoreResult:
    score: int
    reasons: list[str]
    has_conflict: bool


def build_suggested_patch(source: ResolveCandidateSourceItem, athlete: Athlete) -> Optional[SuggestedPatch]:
    patch = SuggestedPatch()

    if source.team and not athlete.club:
        patch.club = source.team.strip()
    if source.city and not athlete.city:
        patch.city = source.city.strip()
    if source.rank and not athlete.license:
        patch.license = source.rank.strip()

    if not patch.model_dump(exclude_none=True):
        return None
    return patch


def score_candidate(source: ResolveCandidateSourceItem, athlete: Athlete) -> ScoreResult:
    score = 0
    reasons: list[str] = []
    has_conflict = False

    source_city = normalize_text(source.city)
    athlete_city = normalize_text(athlete.city)
    source_team = normalize_text(source.team)
    athlete_club = normalize_text(athlete.club)

    if source_city:
        if athlete_city:
            if source_city == athlete_city:
                score += 140
                reasons.append("same city")
            else:
                score -= 90
                has_conflict = True
        else:
            score -= 20

    if source_team:
        if athlete_club:
            if source_team == athlete_club:
                score += 140
                reasons.append("same team/club")
            else:
                source_team_tokens = tokenize(source.team)
                athlete_club_tokens = tokenize(athlete.club)
                if source_team_tokens and source_team_tokens.issubset(athlete_club_tokens):
                    score += 90
                    reasons.append("team tokens match club")
                elif source_team_tokens & athlete_club_tokens:
                    score += 45
                    reasons.append("partial team/club token match")
                else:
                    score -= 70
                    has_conflict = True
        else:
            score -= 20

    if source.city and athlete.club:
        source_city_tokens = tokenize(source.city)
        athlete_club_tokens = tokenize(athlete.club)
        if source_city_tokens and source_city_tokens.issubset(athlete_club_tokens):
            score += 60
            reasons.append("city tokens appear in club")
        elif source_city_tokens & athlete_club_tokens:
            score += 25
            reasons.append("city partially appears in club")

    if athlete.city and athlete.club:
        score += 10

    return ScoreResult(score=score, reasons=reasons, has_conflict=has_conflict)


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

    candidate = ResolveCandidateItem(
        id=athlete.id,
        last_name=athlete.last_name,
        first_name=athlete.first_name,
        birth_year=int(athlete.birth_year),
        gender=athlete.gender,
        city=athlete.city,
        club=athlete.club,
        license=athlete.license,
        score=score_result.score,
        reasons=score_result.reasons,
        suggested_patch=suggested_patch,
    )
    return candidate, score_result.has_conflict


def source_cache_key(source: ResolveCandidateSourceItem) -> tuple[str, ...]:
    return (
        normalize_text(source.last_name),
        normalize_text(source.first_name),
        str(source.birth_year),
        normalize_gender(source.gender) or "",
        normalize_text(source.city),
        normalize_text(source.team),
        normalize_text(source.rank),
    )
