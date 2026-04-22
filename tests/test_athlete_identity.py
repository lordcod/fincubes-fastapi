from app.models.athlete.athlete import Athlete
from app.schemas.athlete.review import ResolveCandidateSourceItem
from app.shared.utils.athlete_identity import (
    AUTO_MATCH_THRESHOLD,
    build_suggested_patch,
    is_same_candidate,
    score_candidate,
)


def make_athlete(**overrides):
    base = {
        "id": 1,
        "last_name": "Сафронова",
        "first_name": "Ольга",
        "birth_year": "2012",
        "gender": "F",
        "city": "Клин",
        "club": 'МАУ ДО "КСШОР им. М.В. Трефилова"',
        "license": "III",
    }
    return Athlete(**(base | overrides))


def make_source(**overrides):
    base = {
        "external_id": "0",
        "last_name": "Сафронова",
        "first_name": "Ольга",
        "birth_year": 2012,
        "gender": "F",
        "city": "Клин",
        "team": 'МАУ ДО "КСШОР им. М.В. Трефилова"',
        "rank": "III",
    }
    return ResolveCandidateSourceItem(**(base | overrides))


def test_is_same_candidate_requires_exact_name_birth_year_and_gender():
    source = make_source()

    assert is_same_candidate(source, make_athlete())
    assert not is_same_candidate(source, make_athlete(birth_year="2011"))
    assert not is_same_candidate(source, make_athlete(first_name="Анна"))
    assert not is_same_candidate(source, make_athlete(gender="M"))


def test_score_candidate_rewards_exact_city_and_team_match():
    source = make_source()
    athlete = make_athlete()

    result = score_candidate(source, athlete)

    assert result.score >= AUTO_MATCH_THRESHOLD
    assert "same city" in result.reasons
    assert "same team/club" in result.reasons
    assert result.has_conflict is False


def test_score_candidate_penalizes_missing_fields_but_keeps_candidate():
    source = make_source()
    athlete = make_athlete(city=None, club=None)

    result = score_candidate(source, athlete)

    assert result.score < AUTO_MATCH_THRESHOLD
    assert result.has_conflict is False


def test_score_candidate_marks_conflict_for_different_city_and_team():
    source = make_source()
    athlete = make_athlete(city="Тверь", club="СШОР Юность")

    result = score_candidate(source, athlete)

    assert result.has_conflict is True
    assert result.score < 0


def test_build_suggested_patch_fills_only_empty_candidate_fields():
    source = make_source(city="Саратов", team="Айсберг Саратов", rank="II")
    athlete = make_athlete(city=None, club=None, license="III")

    patch = build_suggested_patch(source, athlete)

    assert patch is not None
    assert patch.city == "Саратов"
    assert patch.club == "Айсберг Саратов"
    assert patch.license is None
