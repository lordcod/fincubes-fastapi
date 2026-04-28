import asyncio

import pytest

from app.core.errors import APIError, ErrorCode
from app.models.athlete.athlete import Athlete
from app.schemas.athlete.review import (
    ReviewApplyDecisionItem,
    ResolveCandidateSourceItem,
    ResolveCandidatesResponseItem,
    ResolvePreviewDecision,
    ResolvePreviewRequest,
)
from app.schemas.results.result import BulkCreateResult
from app.services.athlete_identity.apply import (
    apply_review_decision,
    is_review_item_resolved,
    maybe_complete_session,
    safe_patch_payload,
    validate_result_upload_resolution,
)
from app.services.athlete_identity.candidate_search import resolve_source_candidates
from app.services.athlete_identity.decision_engine import decide_identity
from app.services.athlete_identity.normalizer import (
    classify_team_kind,
    is_empty_value,
    is_meaningful_value,
    is_weak_value,
)
from app.services.athlete_identity.preview import build_preview
from app.shared.enums.enums import ReviewConfidenceEnum, ReviewDecisionActionEnum
from app.shared.utils.athlete_identity import (
    AUTO_MATCH_THRESHOLD,
    build_suggested_patch,
    is_same_candidate,
    score_candidate,
    to_candidate_response,
)


class FakeAthleteQuery:
    def __init__(self, athletes):
        self._athletes = athletes

    def filter(self, **kwargs):
        filtered = [
            athlete
            for athlete in self._athletes
            if all(
                getattr(athlete, key[:-4]) in value if key.endswith("__in") else getattr(athlete, key) == value
                for key, value in kwargs.items()
            )
        ]
        return FakeAthleteQuery(filtered)

    async def limit(self, limit):
        return self._athletes[:limit]

    async def all(self):
        return self._athletes


class FakeValuesQuery:
    def __init__(self, rows):
        self._rows = rows

    async def values(self, *fields):
        return [{field: row.get(field) for field in fields} for row in self._rows]


class FakeReviewSession:
    def __init__(self, status):
        self.status = status

    async def save(self, update_fields=None):
        self.saved_update_fields = update_fields


class FakeReviewItem:
    def __init__(
        self,
        *,
        id=1,
        external_id="ext-1",
        status="needs_manual_review",
        selected_athlete_id=None,
        source_payload=None,
        candidates_snapshot=None,
        note=None,
    ):
        self.id = id
        self.external_id = external_id
        self.status = status
        self.selected_athlete_id = selected_athlete_id
        self.source_payload = source_payload or make_source().model_dump(mode="json")
        self.candidates_snapshot = candidates_snapshot or []
        self.note = note

    async def save(self, update_fields=None):
        self.saved_update_fields = update_fields


class FakeCountQuery:
    def __init__(self, remaining):
        self.remaining = remaining

    def exclude(self, **kwargs):
        return self

    async def count(self):
        return self.remaining


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


def test_empty_placeholders_are_detected():
    assert is_empty_value(None) is True
    assert is_empty_value("") is True
    assert is_empty_value("-") is True
    assert is_empty_value("—") is True
    assert is_empty_value("Клин") is False


def test_weak_vs_meaningful_values_are_classified():
    assert is_weak_value("Клин") is True
    assert is_weak_value("Сборная Москвы") is True
    assert is_meaningful_value("СШОР Клин") is True
    assert is_meaningful_value("Спортивная школа Олимп") is True


def test_team_kind_classification_covers_required_kinds():
    assert classify_team_kind(None) == "unknown"
    assert classify_team_kind("СШОР Клин") == "club"
    assert classify_team_kind("Клин") == "city"
    assert classify_team_kind("Московская область") == "region"
    assert classify_team_kind("Сборная Москвы") == "generic"


def test_score_candidate_rewards_exact_city_and_team_match():
    source = make_source()
    athlete = make_athlete()

    result = score_candidate(source, athlete)

    assert result.score >= AUTO_MATCH_THRESHOLD
    assert result.signals["city_match"] is True
    assert result.signals["club_exact_match"] is True
    assert result.signals["club_conflict"] is False


def test_city_or_generic_team_does_not_become_club_conflict():
    source = make_source(team="Клин")
    athlete = make_athlete(club="СШОР Клин")

    result = score_candidate(source, athlete)

    assert result.signals["team_kind"] == "city"
    assert result.signals["existing_more_specific"] is True
    assert result.signals["club_conflict"] is False


def test_meaningful_different_clubs_create_club_conflict():
    source = make_source(team="СШОР Клин")
    athlete = make_athlete(club="СШОР Юность")

    result = score_candidate(source, athlete)

    assert result.signals["source_team_meaningful"] is True
    assert result.signals["candidate_club_meaningful"] is True
    assert result.signals["club_conflict"] is True
    assert "different meaningful clubs" in result.conflicts


def test_source_more_specific_when_existing_club_is_empty_or_weak():
    source = make_source(team="СШОР Клин", rank="II")
    athlete = make_athlete(club="-", license=None)

    result = score_candidate(source, athlete)
    patch = build_suggested_patch(source, athlete)

    assert result.signals["source_more_specific"] is True
    assert result.signals["safe_enrich_club"] is True
    assert patch is not None
    assert patch.club == "СШОР Клин"
    assert patch.license == "II"


def test_existing_more_specific_when_source_team_is_weak():
    source = make_source(team="Клин")
    athlete = make_athlete(club='МАУ ДО "КСШОР им. М.В. Трефилова"')

    result = score_candidate(source, athlete)

    assert result.signals["existing_more_specific"] is True
    assert result.signals["club_conflict"] is False


def test_candidate_response_includes_explicit_signals():
    source = make_source(team="СШОР Клин")
    athlete = make_athlete(city="Тверь", club="СШОР Юность")

    candidate, has_conflict = to_candidate_response(source, athlete)

    assert has_conflict is True
    assert candidate.athlete_id == athlete.id
    assert candidate.confidence == ReviewConfidenceEnum.LOW
    assert candidate.signals["name_match"] is True
    assert candidate.signals["birth_year_match"] is True
    assert candidate.signals["gender_match"] is True
    assert candidate.signals["city_conflict"] is True
    assert candidate.signals["club_conflict"] is True


def test_high_confidence_requires_strict_single_candidate_context():
    source = make_source()
    candidate, _ = to_candidate_response(source, make_athlete())

    decision = decide_identity([candidate])

    assert decision.action == ReviewDecisionActionEnum.MATCH_EXISTING
    assert decision.athlete_id == candidate.id
    assert decision.confidence == ReviewConfidenceEnum.HIGH


def test_enrich_existing_requires_no_city_or_club_conflict():
    source = make_source(team="СШОР Клин", rank="II")
    candidate, _ = to_candidate_response(
        source,
        make_athlete(club="-", license=None),
    )

    decision = decide_identity([candidate])

    assert decision.action == ReviewDecisionActionEnum.ENRICH_EXISTING
    assert decision.confidence == ReviewConfidenceEnum.MEDIUM
    assert decision.suggested_patch is not None
    assert decision.suggested_patch.club == "СШОР Клин"


def test_create_new_on_meaningful_club_conflict():
    source = make_source(team="СШОР Клин")
    candidate, _ = to_candidate_response(
        source,
        make_athlete(city="Клин", club="СШОР Юность"),
    )

    decision = decide_identity([candidate])

    assert decision.action == ReviewDecisionActionEnum.CREATE_NEW
    assert "different meaningful clubs" in decision.conflicts


def test_decision_does_not_depend_primarily_on_score():
    source = make_source(city="Клин", team="СШОР Клин")
    candidate, _ = to_candidate_response(
        source,
        make_athlete(city="Клин", club="СШОР Юность"),
    )
    boosted_candidate = candidate.model_copy(update={"score": 999})

    decision = decide_identity([boosted_candidate])

    assert decision.action == ReviewDecisionActionEnum.CREATE_NEW
    assert decision.confidence == ReviewConfidenceEnum.LOW


def test_multiple_candidates_require_manual_review():
    source = make_source()
    first, _ = to_candidate_response(source, make_athlete(id=1))
    second, _ = to_candidate_response(source, make_athlete(id=2))

    decision = decide_identity([first, second])

    assert decision.action == ReviewDecisionActionEnum.MANUAL
    assert "ambiguous candidates" in decision.conflicts


def test_safe_patch_payload_does_not_overwrite_meaningful_fields():
    athlete = make_athlete(city="Клин", club="СШОР Юность", license="III")

    changes = safe_patch_payload(
        {"city": "Тверь", "club": "Новый клуб", "license": "II"},
        athlete,
    )

    assert changes == {}


def test_safe_patch_payload_can_upgrade_weak_club():
    athlete = make_athlete(club="Клин", city="Клин", license="III")

    changes = safe_patch_payload(
        {"club": "СШОР Клин", "city": "Тверь", "license": "II"},
        athlete,
    )

    assert changes == {"club": "СШОР Клин"}


def test_result_upload_resolution_requires_review_session():
    with pytest.raises(APIError) as exc:
        asyncio.run(validate_result_upload_resolution({1}, None))

    assert exc.value.error_name == ErrorCode.REVIEW_SESSION_NOT_FOUND.name


def test_resolve_source_candidates_returns_formal_signals(monkeypatch):
    athlete = make_athlete(club="-", license=None)
    monkeypatch.setattr(
        "app.services.athlete_identity.candidate_search.Athlete.filter",
        lambda **kwargs: FakeAthleteQuery([athlete]),
    )

    resolution = asyncio.run(resolve_source_candidates(make_source(team="СШОР Клин", rank="II")))

    assert resolution.decision.action == ReviewDecisionActionEnum.ENRICH_EXISTING
    assert resolution.recommended_action == "enrich_existing"
    assert resolution.candidates[0].signals["team_kind"] == "club"
    assert resolution.candidates[0].signals["source_team_meaningful"] is True
    assert resolution.candidates[0].signals["safe_enrich_club"] is True
    assert "city" not in resolution.candidates[0].signals
    assert "team" not in resolution.candidates[0].signals


def test_resolve_source_candidates_populates_conflicts_for_meaningful_club_conflict(monkeypatch):
    athlete = make_athlete(club="СШОР Юность")
    monkeypatch.setattr(
        "app.services.athlete_identity.candidate_search.Athlete.filter",
        lambda **kwargs: FakeAthleteQuery([athlete]),
    )

    resolution = asyncio.run(resolve_source_candidates(make_source(team="СШОР Клин")))

    assert resolution.decision.action == ReviewDecisionActionEnum.CREATE_NEW
    assert resolution.recommended_action == "create_new"
    assert resolution.decision.conflicts == ["different meaningful clubs"]
    assert resolution.candidates[0].suggested_patch is None


def test_resolve_candidates_response_item_uses_normalized_recommended_action(monkeypatch):
    athlete = make_athlete(id=7)
    monkeypatch.setattr(
        "app.services.athlete_identity.candidate_search.Athlete.filter",
        lambda **kwargs: FakeAthleteQuery([athlete]),
    )

    resolution = asyncio.run(resolve_source_candidates(make_source(external_id="ext-1", team="Клин")))
    response_item = ResolveCandidatesResponseItem(
        external_id="ext-1",
        candidates=resolution.candidates,
        auto_match=resolution.auto_match,
        confidence=resolution.decision.confidence,
        recommended_action=resolution.recommended_action,
        recommended_athlete_id=resolution.decision.athlete_id,
        reasons=resolution.decision.reasons,
        conflicts=resolution.decision.conflicts,
    )

    assert response_item.external_id == "ext-1"
    assert response_item.recommended_action == "manual_review"
    assert response_item.recommended_athlete_id == 7
    assert response_item.confidence == resolution.decision.confidence
    assert response_item.candidates[0].signals["existing_more_specific"] is True
    assert "team" not in response_item.candidates[0].signals


def test_preview_enrich_existing_matches_safe_patch_rules(monkeypatch):
    athlete = make_athlete(club="-", license=None)
    monkeypatch.setattr(
        "app.services.athlete_identity.preview.Athlete.filter",
        lambda **kwargs: FakeAthleteQuery([athlete]),
    )

    preview = asyncio.run(
        build_preview(
            ResolvePreviewRequest(
                items=[
                    ResolvePreviewDecision(
                        external_id="ext-1",
                        action="enrich_existing",
                        athlete_id=athlete.id,
                        source=make_source(team="СШОР Клин", rank="II"),
                    )
                ]
            )
        )
    )

    item = preview.items[0]
    assert item.action == "enrich_existing"
    assert item.resolved is True
    assert item.athlete_id == athlete.id
    assert item.update_payload is not None
    assert item.update_payload.club == "СШОР Клин"
    assert item.update_payload.license == "II"
    assert item.conflicts == []


def test_preview_rejects_update_for_club_conflict(monkeypatch):
    athlete = make_athlete(club="СШОР Юность")
    monkeypatch.setattr(
        "app.services.athlete_identity.preview.Athlete.filter",
        lambda **kwargs: FakeAthleteQuery([athlete]),
    )

    preview = asyncio.run(
        build_preview(
            ResolvePreviewRequest(
                items=[
                    ResolvePreviewDecision(
                        external_id="ext-2",
                        action="enrich_existing",
                        athlete_id=athlete.id,
                        source=make_source(team="СШОР Клин"),
                    )
                ]
            )
        )
    )

    item = preview.items[0]
    assert item.action == "manual_review"
    assert item.resolved is False
    assert item.update_payload is None
    assert "different meaningful clubs" in item.conflicts


def test_preview_normalizes_old_action_values(monkeypatch):
    athlete = make_athlete(id=9)
    monkeypatch.setattr(
        "app.services.athlete_identity.preview.Athlete.filter",
        lambda **kwargs: FakeAthleteQuery([athlete]),
    )

    preview = asyncio.run(
        build_preview(
            ResolvePreviewRequest(
                items=[
                    ResolvePreviewDecision(
                        external_id="ext-3",
                        action="match",
                        athlete_id=athlete.id,
                        source=make_source(),
                    ),
                    ResolvePreviewDecision(
                        external_id="ext-4",
                        action="manual",
                        source=make_source(),
                    ),
                ]
            )
        )
    )

    assert preview.items[0].action == "match_existing"
    assert preview.items[1].action == "manual_review"


def test_preview_output_uses_only_new_action_names(monkeypatch):
    athlete = make_athlete(id=11)
    monkeypatch.setattr(
        "app.services.athlete_identity.preview.Athlete.filter",
        lambda **kwargs: FakeAthleteQuery([athlete]),
    )

    preview = asyncio.run(
        build_preview(
            ResolvePreviewRequest(
                items=[
                    ResolvePreviewDecision(
                        external_id="ext-5",
                        action="match",
                        athlete_id=athlete.id,
                        source=make_source(team="Клин"),
                    ),
                    ResolvePreviewDecision(
                        external_id="ext-6",
                        action="create_new",
                        source=make_source(gender=None),
                    ),
                ]
            )
        )
    )

    assert {item.action for item in preview.items}.issubset(
        {"match_existing", "enrich_existing", "create_new", "manual_review"}
    )
    assert preview.items[1].action == "manual_review"
    assert preview.items[1].resolved is False


def test_apply_safe_patch_and_preview_safe_patch_are_consistent(monkeypatch):
    athlete = make_athlete(club="Клин", city="Клин", license=None)
    monkeypatch.setattr(
        "app.services.athlete_identity.preview.Athlete.filter",
        lambda **kwargs: FakeAthleteQuery([athlete]),
    )

    preview = asyncio.run(
        build_preview(
            ResolvePreviewRequest(
                items=[
                    ResolvePreviewDecision(
                        external_id="ext-7",
                        action="enrich_existing",
                        athlete_id=athlete.id,
                        source=make_source(team="СШОР Клин", rank="II"),
                    )
                ]
            )
        )
    )

    item = preview.items[0]
    assert item.update_payload is not None
    assert safe_patch_payload(item.update_payload.model_dump(exclude_none=True), athlete) == item.update_payload.model_dump(exclude_none=True)


def test_result_upload_passes_when_every_external_id_maps_to_same_athlete_id(monkeypatch):
    monkeypatch.setattr(
        "app.services.athlete_identity.apply.ReviewSession.get_or_none",
        lambda **kwargs: asyncio.sleep(0, result=FakeReviewSession("completed")),
    )
    monkeypatch.setattr(
        "app.services.athlete_identity.apply.ReviewItem.filter",
        lambda **kwargs: FakeValuesQuery(
            [
                {"external_id": "ext-1", "selected_athlete_id": 10, "status": "matched_existing"},
                {"external_id": "ext-2", "selected_athlete_id": 11, "status": "created_new"},
            ]
        ),
    )

    asyncio.run(
        validate_result_upload_resolution(
            [
                BulkCreateResult(external_id="ext-1", competition_id=1, athlete_id=10, results=[]),
                BulkCreateResult(external_id="ext-2", competition_id=1, athlete_id=11, results=[]),
            ],
            1,
        )
    )


def test_result_upload_fails_when_external_id_is_missing_and_resolution_required(monkeypatch):
    monkeypatch.setattr(
        "app.services.athlete_identity.apply.ReviewSession.get_or_none",
        lambda **kwargs: asyncio.sleep(0, result=FakeReviewSession("completed")),
    )

    with pytest.raises(APIError) as exc:
        asyncio.run(
            validate_result_upload_resolution(
                [BulkCreateResult(external_id=None, competition_id=1, athlete_id=10, results=[])],
                1,
            )
        )

    assert exc.value.error_name == ErrorCode.REVIEW_ITEM_NOT_FOUND.name


def test_result_upload_fails_when_external_id_is_unresolved(monkeypatch):
    monkeypatch.setattr(
        "app.services.athlete_identity.apply.ReviewSession.get_or_none",
        lambda **kwargs: asyncio.sleep(0, result=FakeReviewSession("completed")),
    )
    monkeypatch.setattr(
        "app.services.athlete_identity.apply.ReviewItem.filter",
        lambda **kwargs: FakeValuesQuery([]),
    )

    with pytest.raises(APIError) as exc:
        asyncio.run(
            validate_result_upload_resolution(
                [BulkCreateResult(external_id="ext-3", competition_id=1, athlete_id=10, results=[])],
                1,
            )
        )

    assert exc.value.error_name == ErrorCode.REVIEW_ITEM_NOT_FOUND.name


def test_result_upload_fails_when_athlete_id_does_not_match_resolved_mapping(monkeypatch):
    monkeypatch.setattr(
        "app.services.athlete_identity.apply.ReviewSession.get_or_none",
        lambda **kwargs: asyncio.sleep(0, result=FakeReviewSession("completed")),
    )
    monkeypatch.setattr(
        "app.services.athlete_identity.apply.ReviewItem.filter",
        lambda **kwargs: FakeValuesQuery(
            [{"external_id": "ext-4", "selected_athlete_id": 99, "status": "matched_existing"}]
        ),
    )

    with pytest.raises(APIError) as exc:
        asyncio.run(
            validate_result_upload_resolution(
                [BulkCreateResult(external_id="ext-4", competition_id=1, athlete_id=10, results=[])],
                1,
            )
        )

    assert exc.value.error_name == ErrorCode.REVIEW_ITEM_NOT_FOUND.name


def test_old_behavior_still_works_when_require_resolution_false():
    result_item = BulkCreateResult(competition_id=1, athlete_id=10, results=[])
    assert result_item.external_id is None


def test_session_cannot_complete_with_unresolved_manual_review_item(monkeypatch):
    session = FakeReviewSession("active")
    monkeypatch.setattr(
        "app.services.athlete_identity.apply.ReviewItem.filter",
        lambda **kwargs: FakeCountQuery(1),
    )

    asyncio.run(maybe_complete_session(session))

    assert session.status == "active"


def test_apply_create_new_sets_selected_athlete_id(monkeypatch):
    created_athlete = make_athlete(id=77)
    item = FakeReviewItem(id=10, external_id="ext-create", status="needs_manual_review")
    created_payloads = []

    async def fake_create(**kwargs):
        created_payloads.append(kwargs)
        return created_athlete

    async def fake_review_decision_create(**kwargs):
        return kwargs

    monkeypatch.setattr("app.services.athlete_identity.apply.Athlete.create", fake_create)
    monkeypatch.setattr("app.services.athlete_identity.apply.ReviewDecision.create", fake_review_decision_create)

    result = asyncio.run(
        apply_review_decision(
            item,
            ReviewApplyDecisionItem(
                review_item_id=item.id,
                action=ReviewDecisionActionEnum.CREATE_NEW,
            ),
        )
    )

    assert item.selected_athlete_id == 77
    assert is_review_item_resolved(item.status) is True
    assert result.action == "create_new"
    assert result.selected_athlete_id == 77
    assert created_payloads


def test_apply_enrich_existing_sets_selected_athlete_id_and_updated_fields(monkeypatch):
    athlete = make_athlete(id=88, club="-", license=None)

    async def fake_save(update_fields=None):
        athlete.saved_update_fields = update_fields

    athlete.save = fake_save
    item = FakeReviewItem(
        id=11,
        external_id="ext-enrich",
        status="auto_match_candidate",
        selected_athlete_id=88,
        candidates_snapshot=[
            {
                "athlete_id": 88,
                "reasons": ["source club is more specific than existing club"],
                "conflicts": [],
                "suggested_patch": {"club": "СШОР Клин", "license": "II"},
            }
        ],
    )

    async def fake_get_or_none(**kwargs):
        return athlete

    async def fake_review_decision_create(**kwargs):
        return kwargs

    monkeypatch.setattr("app.services.athlete_identity.apply.Athlete.get_or_none", fake_get_or_none)
    monkeypatch.setattr("app.services.athlete_identity.apply.ReviewDecision.create", fake_review_decision_create)

    result = asyncio.run(
        apply_review_decision(
            item,
            ReviewApplyDecisionItem(
                review_item_id=item.id,
                action=ReviewDecisionActionEnum.ENRICH_EXISTING,
                athlete_id=88,
                patch={"club": "СШОР Клин", "license": "II"},
            ),
        )
    )

    assert item.selected_athlete_id == 88
    assert result.action == "enrich_existing"
    assert result.selected_athlete_id == 88
    assert result.updated_fields == ["club", "license"]
    assert result.resolved is True


def test_completed_session_provides_mapping_usable_by_result_upload_gating(monkeypatch):
    session = FakeReviewSession("completed")
    monkeypatch.setattr(
        "app.services.athlete_identity.apply.ReviewSession.get_or_none",
        lambda **kwargs: asyncio.sleep(0, result=session),
    )
    monkeypatch.setattr(
        "app.services.athlete_identity.apply.ReviewItem.filter",
        lambda **kwargs: FakeValuesQuery(
            [{"external_id": "ext-map", "selected_athlete_id": 42, "status": "created_new"}]
        ),
    )

    asyncio.run(
        validate_result_upload_resolution(
            [BulkCreateResult(external_id="ext-map", competition_id=1, athlete_id=42, results=[])],
            1,
        )
    )


def test_manual_review_blocks_completion(monkeypatch):
    session = FakeReviewSession("active")
    item = FakeReviewItem(id=12, external_id="ext-manual", status="auto_match_candidate", selected_athlete_id=5)

    async def fake_review_decision_create(**kwargs):
        return kwargs

    monkeypatch.setattr("app.services.athlete_identity.apply.ReviewDecision.create", fake_review_decision_create)
    result = asyncio.run(
        apply_review_decision(
            item,
            ReviewApplyDecisionItem(
                review_item_id=item.id,
                action=ReviewDecisionActionEnum.MANUAL,
                note="needs human review",
            ),
        )
    )
    monkeypatch.setattr(
        "app.services.athlete_identity.apply.ReviewItem.filter",
        lambda **kwargs: FakeCountQuery(1),
    )

    asyncio.run(maybe_complete_session(session))

    assert result.action == "manual_review"
    assert result.resolved is False
    assert item.selected_athlete_id is None
    assert session.status == "active"
