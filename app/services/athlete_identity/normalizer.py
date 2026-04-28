import re
from typing import Optional

from app.schemas.athlete.review import ResolveCandidateSourceItem

TOKEN_RE = re.compile(r"[0-9A-Za-zА-Яа-яЁё]+")
EMPTY_PLACEHOLDERS = {"", "-", "—"}
TEAM_KIND_UNKNOWN = "unknown"
TEAM_KIND_CLUB = "club"
TEAM_KIND_CITY = "city"
TEAM_KIND_REGION = "region"
TEAM_KIND_GENERIC = "generic"

CLUB_MARKERS = (
    "сшор",
    "ксшор",
    "сш",
    "ск",
    "цсп",
    "цска",
    "дюсш",
    "сдюсшор",
    "спортивная школа",
    "школа олимпийского резерва",
    "клуб",
    "академия",
    "училище олимпийского резерва",
)
REGION_MARKERS = (
    "область",
    "обл",
    "край",
    "республика",
    "респ",
    "округ",
    "район",
)
GENERIC_TEAM_MARKERS = (
    "сборная",
    "команда",
    "team",
    "участники",
    "участник",
)


def _contains_marker(value: str, markers: tuple[str, ...]) -> bool:
    tokens = tokenize(value)
    for marker in markers:
        if " " in marker:
            if marker in value:
                return True
        elif marker in tokens:
            return True
    return False


def normalize_text(value: Optional[str]) -> str:
    if value is None:
        return ""

    normalized = str(value).strip().lower().replace("ё", "е")
    if normalized in EMPTY_PLACEHOLDERS:
        return ""

    normalized = normalized.replace('"', " ").replace("«", " ").replace("»", " ")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def tokenize(value: Optional[str]) -> set[str]:
    normalized = normalize_text(value)
    return {match.group(0) for match in TOKEN_RE.finditer(normalized)}


def normalize_gender(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    normalized = value.strip().upper()
    return normalized or None


def is_empty_value(value: Optional[str]) -> bool:
    return normalize_text(value) == ""


def classify_team_kind(value: Optional[str]) -> str:
    normalized = normalize_text(value)
    if not normalized:
        return TEAM_KIND_UNKNOWN

    if _contains_marker(normalized, CLUB_MARKERS):
        return TEAM_KIND_CLUB
    if _contains_marker(normalized, REGION_MARKERS):
        return TEAM_KIND_REGION
    if _contains_marker(normalized, GENERIC_TEAM_MARKERS):
        return TEAM_KIND_GENERIC

    tokens = tokenize(normalized)
    if tokens and len(tokens) <= 3:
        return TEAM_KIND_CITY

    return TEAM_KIND_UNKNOWN


def is_weak_value(value: Optional[str]) -> bool:
    if is_empty_value(value):
        return False
    return classify_team_kind(value) != TEAM_KIND_CLUB


def is_meaningful_value(value: Optional[str]) -> bool:
    return classify_team_kind(value) == TEAM_KIND_CLUB


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
