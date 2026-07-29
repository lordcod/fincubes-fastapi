from collections.abc import Iterable

from tortoise.backends.base.client import BaseDBAsyncClient
from tortoise.transactions import in_transaction

from app.core.errors import APIError, ErrorCode
from app.models.athlete.athlete import Athlete
from app.models.competition.competition import Competition
from app.models.competition.relay_leg import RelayLeg
from app.models.competition.relay_result import RelayResult
from app.schemas.results.relay import (
    RelayLeg_Pydantic,
    RelayResultCreate,
    RelayResultWithLegs,
)


def validate_relay_composition(payload: RelayResultCreate) -> None:
    if payload.relay_count <= 1:
        raise APIError(ErrorCode.RELAY_COUNT_INVALID)

    if len(payload.legs) != payload.relay_count:
        raise APIError(ErrorCode.RELAY_ATHLETE_COUNT_MISMATCH)

    orders = [leg.order for leg in payload.legs]
    if sorted(orders) != list(range(1, payload.relay_count + 1)):
        raise APIError(ErrorCode.RELAY_LEG_ORDER_INVALID)

    athlete_ids = [leg.athlete_id for leg in payload.legs]
    if len(set(athlete_ids)) != len(athlete_ids):
        raise APIError(ErrorCode.RELAY_ATHLETE_DUPLICATE)


def _serialize_relay_leg(leg: RelayLeg) -> RelayLeg_Pydantic:
    return RelayLeg_Pydantic.model_validate(
        {
            "id": leg.id,
            "created_at": leg.created_at,
            "updated_at": leg.updated_at,
            "relay_result_id": leg.relay_result_id,
            "athlete_id": leg.athlete_id,
            "order": leg.order,
            "result": leg.result,
            "metadata": leg.metadata,
        }
    )


def serialize_relay_result(
    relay_result: RelayResult,
    legs: Iterable[RelayLeg],
) -> RelayResultWithLegs:
    return RelayResultWithLegs.model_validate(
        {
            "id": relay_result.id,
            "created_at": relay_result.created_at,
            "updated_at": relay_result.updated_at,
            "competition_id": relay_result.competition_id,
            "name": relay_result.name,
            "stroke": relay_result.stroke,
            "distance": relay_result.distance,
            "relay_count": relay_result.relay_count,
            "gender": relay_result.gender,
            "result": relay_result.result,
            "place": relay_result.place,
            "points": relay_result.points,
            "status": relay_result.status,
            "metadata": relay_result.metadata,
            "legs": [_serialize_relay_leg(leg) for leg in legs],
        }
    )


async def _create_relay_result(
    payload: RelayResultCreate,
    db: BaseDBAsyncClient,
) -> RelayResultWithLegs:
    validate_relay_composition(payload)

    competition = await Competition.get_or_none(
        id=payload.competition_id,
    ).using_db(db)
    if competition is None:
        raise APIError(ErrorCode.COMPETITION_NOT_FOUND)

    athlete_ids = [leg.athlete_id for leg in payload.legs]
    athletes = await Athlete.filter(id__in=athlete_ids).using_db(db)
    athletes_by_id = {athlete.id: athlete for athlete in athletes}
    if len(athletes_by_id) != len(athlete_ids):
        raise APIError(ErrorCode.ATHLETE_NOT_FOUND)

    relay_data = payload.model_dump(
        exclude={"competition_id", "legs"},
    )
    relay_result = await RelayResult.create(
        competition=competition,
        using_db=db,
        **relay_data,
    )

    relay_legs = [
        RelayLeg(
            relay_result=relay_result,
            athlete=athletes_by_id[leg.athlete_id],
            order=leg.order,
            result=leg.result,
            metadata=leg.metadata,
        )
        for leg in payload.legs
    ]
    await RelayLeg.bulk_create(relay_legs, using_db=db)

    saved_legs = await RelayLeg.filter(
        relay_result_id=relay_result.id,
    ).using_db(db).order_by("order")
    return serialize_relay_result(relay_result, saved_legs)


async def create_relay_result(
    payload: RelayResultCreate,
) -> RelayResultWithLegs:
    async with in_transaction() as db:
        return await _create_relay_result(payload, db)


async def bulk_create_relay_results(
    payloads: list[RelayResultCreate],
) -> list[RelayResultWithLegs]:
    if not payloads:
        raise APIError(ErrorCode.EMPTY_DATA)

    for payload in payloads:
        validate_relay_composition(payload)

    async with in_transaction() as db:
        return [
            await _create_relay_result(payload, db)
            for payload in payloads
        ]


async def get_relay_result(
    relay_result_id: int,
) -> RelayResultWithLegs:
    relay_result = await RelayResult.get_or_none(id=relay_result_id)
    if relay_result is None:
        raise APIError(ErrorCode.RELAY_RESULT_NOT_FOUND)

    legs = await RelayLeg.filter(
        relay_result_id=relay_result.id,
    ).order_by("order")
    return serialize_relay_result(relay_result, legs)


async def list_relay_results(
    competition_id: int,
    stroke: str | None = None,
    distance: int | None = None,
    relay_count: int | None = None,
    gender: str | None = None,
) -> list[RelayResultWithLegs]:
    if not await Competition.filter(id=competition_id).exists():
        raise APIError(ErrorCode.COMPETITION_NOT_FOUND)

    filters = {"competition_id": competition_id}
    if stroke is not None:
        filters["stroke"] = stroke
    if distance is not None:
        filters["distance"] = distance
    if relay_count is not None:
        filters["relay_count"] = relay_count
    if gender is not None:
        filters["gender"] = gender

    relay_results = await RelayResult.filter(**filters).order_by("id")
    if not relay_results:
        return []

    result_ids = [result.id for result in relay_results]
    legs = await RelayLeg.filter(
        relay_result_id__in=result_ids,
    ).order_by("relay_result_id", "order")

    legs_by_result: dict[int, list[RelayLeg]] = {
        result_id: []
        for result_id in result_ids
    }
    for leg in legs:
        legs_by_result[leg.relay_result_id].append(leg)

    return [
        serialize_relay_result(
            relay_result,
            legs_by_result[relay_result.id],
        )
        for relay_result in relay_results
    ]


async def delete_relay_result(relay_result_id: int) -> None:
    deleted_count = await RelayResult.filter(id=relay_result_id).delete()
    if deleted_count == 0:
        raise APIError(ErrorCode.RELAY_RESULT_NOT_FOUND)
