import asyncio
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastfsx import FileRouter
from pydantic import ValidationError
from tortoise import Tortoise

from app.core.errors import APIError, ErrorCode
from app.models.athlete.athlete import Athlete
from app.models.competition.competition import Competition
from app.models.competition.distance import Distance
from app.models.competition.relay_leg import RelayLeg
from app.models.competition.relay_result import RelayResult
from app.models.competition.result import Result
from app.schemas.competition.distance import DistanceIn_Pydantic
from app.schemas.athlete.performance import UserPerformance
from app.schemas.results.relay import (
    RelayResultCreate,
    RelayResult_Pydantic,
)
from app.services.relay_results import (
    bulk_create_relay_results,
    create_relay_result,
    delete_relay_result,
    get_relay_result,
    list_relay_results,
    validate_relay_composition,
)
from app.services.athlete_performances import build_athlete_performances
from app.shared.enums.enums import EventTypeEnum, GenderEnum


def _relay_create_payload(**updates) -> RelayResultCreate:
    data = {
        "competition_id": 1,
        "name": "СШ ВВС",
        "stroke": "SURFACE",
        "distance": 50,
        "relay_count": 4,
        "gender": "M",
        "result": "01:40.30",
        "place": "1",
        "points": "50",
        "status": "COMPLETED",
        "metadata": None,
        "legs": [
            {
                "athlete_id": athlete_id,
                "order": athlete_id,
                "result": f"00:2{athlete_id}.00",
                "metadata": None,
            }
            for athlete_id in range(1, 5)
        ],
    }
    data.update(updates)
    return RelayResultCreate.model_validate(data)


def test_distance_total_distance_uses_relay_count():
    distance = Distance(
        competition_id=1,
        order=1,
        stroke="SURFACE",
        distance=50,
        relay_count=4,
        gender="M",
    )

    assert distance.total_distance == 200


def test_individual_distance_defaults_to_one_leg():
    distance = Distance(
        competition_id=1,
        order=1,
        stroke="SURFACE",
        distance=100,
        gender="M",
    )

    assert distance.relay_count == 1
    assert distance.total_distance == 100


def test_relay_result_total_distance():
    result = RelayResult(
        competition_id=1,
        name="СШ ВВС",
        stroke="SURFACE",
        distance=50,
        relay_count=4,
        gender="M",
    )

    result.validate_relay()
    assert result.total_distance == 200


@pytest.mark.parametrize(
    ("distance", "relay_count"),
    [
        (0, 4),
        (50, 1),
        (50, 0),
    ],
)
def test_relay_result_rejects_invalid_event(distance, relay_count):
    result = RelayResult(
        competition_id=1,
        name="Команда",
        stroke="SURFACE",
        distance=distance,
        relay_count=relay_count,
        gender="M",
    )

    with pytest.raises(ValueError):
        result.validate_relay()


def test_relay_leg_order_starts_from_one():
    leg = RelayLeg(
        relay_result_id=1,
        athlete_id=1,
        order=0,
    )

    with pytest.raises(ValueError, match="order"):
        leg.validate_order()


def test_distance_input_rejects_non_positive_relay_count():
    with pytest.raises(ValidationError):
        DistanceIn_Pydantic(
            order=1,
            stroke="SURFACE",
            distance=50,
            relay_count=0,
            gender="M",
        )


def test_relay_result_creation_requires_more_than_one_leg():
    payload = _relay_create_payload(
        relay_count=1,
        legs=_relay_create_payload().legs[:1],
    )

    with pytest.raises(APIError) as exc_info:
        validate_relay_composition(payload)

    assert exc_info.value.error_code == ErrorCode.RELAY_COUNT_INVALID.code


def test_relay_result_response_contains_total_distance():
    result = RelayResult_Pydantic(
        id=1,
        created_at="2026-07-29T00:00:00Z",
        updated_at="2026-07-29T00:00:00Z",
        name="СШ ВВС",
        stroke="SURFACE",
        distance=50,
        relay_count=4,
        gender="M",
        result=None,
        place="1",
        points="50",
        status="COMPLETED",
        metadata=None,
        competition_id=1,
    )

    assert result.total_distance == 200
    assert result.model_dump()["total_distance"] == 200


def test_valid_relay_composition():
    validate_relay_composition(_relay_create_payload())


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("F", GenderEnum.FEMALE),
        ("M", GenderEnum.MALE),
        ("X", GenderEnum.MIXED),
        ("A", GenderEnum.ALL),
    ],
)
def test_relay_result_accepts_supported_genders(value, expected):
    payload = _relay_create_payload(gender=value)

    assert payload.gender == expected


def test_relay_result_rejects_unknown_gender():
    with pytest.raises(ValidationError):
        _relay_create_payload(gender="U")


def test_relay_composition_requires_exact_leg_count():
    payload = _relay_create_payload(
        legs=_relay_create_payload().legs[:3],
    )

    with pytest.raises(APIError) as exc_info:
        validate_relay_composition(payload)

    assert (
        exc_info.value.error_code
        == ErrorCode.RELAY_ATHLETE_COUNT_MISMATCH.code
    )


def test_relay_composition_requires_sequential_orders():
    legs = _relay_create_payload().legs
    legs[-1].order = 5
    payload = _relay_create_payload(legs=legs)

    with pytest.raises(APIError) as exc_info:
        validate_relay_composition(payload)

    assert exc_info.value.error_code == ErrorCode.RELAY_LEG_ORDER_INVALID.code


def test_relay_composition_rejects_duplicate_athlete():
    legs = _relay_create_payload().legs
    legs[-1].athlete_id = legs[0].athlete_id
    payload = _relay_create_payload(legs=legs)

    with pytest.raises(APIError) as exc_info:
        validate_relay_composition(payload)

    assert exc_info.value.error_code == ErrorCode.RELAY_ATHLETE_DUPLICATE.code


def test_relay_routes_are_registered():
    app = FastAPI()
    admin_routes_dir = Path("app/pages/admin/relay-results")
    app.include_router(
        FileRouter(admin_routes_dir).build(),
        prefix="/admin/relay-results",
    )
    public_routes_dir = Path("app/pages/public/client/relay-results")
    app.include_router(
        FileRouter(public_routes_dir).build(),
        prefix="/public/client/relay-results",
    )

    paths = app.openapi()["paths"]
    assert "/admin/relay-results/" in paths
    assert "/admin/relay-results/bulk-create/" in paths
    assert "/admin/relay-results/{id}/" in paths
    assert "/public/client/relay-results/" in paths

    gender_schema = app.openapi()["components"]["schemas"]["GenderEnum"]
    assert gender_schema["enum"] == ["F", "M", "X", "A"]


def test_common_performance_contract_exposes_team_and_split_results():
    performance = UserPerformance(
        id=701,
        created_at=datetime(2026, 7, 29, tzinfo=timezone.utc),
        updated_at=datetime(2026, 7, 29, tzinfo=timezone.utc),
        event_type=EventTypeEnum.RELAY,
        stroke="SURFACE",
        distance=50,
        relay_count=4,
        total_distance=200,
        name="СШ ВВС",
        result="01:40.30",
        split_result="00:24.10",
        relay_order=1,
        relay_leg_id=9001,
    )

    data = performance.model_dump(mode="json")
    assert data["event_type"] == "RELAY"
    assert data["result"] == "01:40,30"
    assert data["split_result"] == "00:24,10"


def test_relay_result_service_round_trip():
    async def scenario():
        await Tortoise.init(
            db_url="sqlite://:memory:",
            modules={"models": ["app.models"]},
        )
        await Tortoise.generate_schemas()
        try:
            competition = await Competition.create(
                name="Кубок",
                date="29.07.2026",
                location="Бассейн",
                city="Москва",
                organizer="Организатор",
                course="50",
                status="ACTIVE",
                links=[],
                start_date=date(2026, 7, 29),
                end_date=date(2026, 7, 30),
            )
            athletes = [
                await Athlete.create(
                    last_name=f"Фамилия{index}",
                    first_name=f"Имя{index}",
                    birth_year="2008",
                    gender="M",
                )
                for index in range(1, 5)
            ]
            payload = _relay_create_payload(
                competition_id=competition.id,
                result=None,
                legs=[
                    {
                        "athlete_id": athlete.id,
                        "order": order,
                        "result": None,
                        "metadata": None,
                    }
                    for order, athlete in enumerate(athletes, start=1)
                ],
            )

            created = await create_relay_result(payload)
            assert created.total_distance == 200
            assert [leg.order for leg in created.legs] == [1, 2, 3, 4]

            fetched = await get_relay_result(created.id)
            assert fetched.name == "СШ ВВС"
            assert len(fetched.legs) == 4

            listed = await list_relay_results(competition.id)
            assert [item.id for item in listed] == [created.id]

            await Result.create(
                athlete=athletes[0],
                competition=competition,
                stroke="SURFACE",
                distance=100,
                result=None,
                status="COMPLETED",
            )
            athlete_results = await build_athlete_performances(
                athletes[0].id,
            )
            performances = athlete_results.results[0].performances
            individual = next(
                item
                for item in performances
                if item.event_type == EventTypeEnum.INDIVIDUAL
            )
            relay = next(
                item
                for item in performances
                if item.event_type == EventTypeEnum.RELAY
            )
            assert individual.total_distance == 100
            assert individual.relay_count == 1
            assert relay.name == "СШ ВВС"
            assert relay.total_distance == 200
            assert relay.relay_count == 4
            assert relay.relay_order == 1
            assert relay.relay_leg_id == created.legs[0].id

            await delete_relay_result(created.id)
            with pytest.raises(APIError) as exc_info:
                await get_relay_result(created.id)
            assert (
                exc_info.value.error_code
                == ErrorCode.RELAY_RESULT_NOT_FOUND.code
            )

            invalid_legs = [
                leg.model_copy()
                for leg in payload.legs
            ]
            invalid_legs[-1].athlete_id = 999_999
            invalid_payload = _relay_create_payload(
                competition_id=competition.id,
                name="Несуществующий состав",
                result=None,
                legs=invalid_legs,
            )

            with pytest.raises(APIError) as exc_info:
                await bulk_create_relay_results(
                    [payload, invalid_payload],
                )
            assert (
                exc_info.value.error_code
                == ErrorCode.ATHLETE_NOT_FOUND.code
            )
            assert await RelayResult.all().count() == 0
        finally:
            await Tortoise.close_connections()
            await Tortoise._reset_apps()

    asyncio.run(scenario())
