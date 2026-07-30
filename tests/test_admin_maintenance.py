import asyncio
import importlib.util
from datetime import date
from pathlib import Path

from tortoise import Tortoise

from app.models import Athlete, Competition, RelayLeg, RelayResult, Result
from app.services.admin_maintenance import clear_empty_athletes, clear_results, transfer_results


def _load_athlete_route_module():
    route_path = Path("app/pages/public/server/athlete/[id]/route.py")
    spec = importlib.util.spec_from_file_location("athlete_detail_route", route_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


async def _create_competition() -> Competition:
    return await Competition.create(
        name="Cup",
        date="30.07.2026",
        location="Pool",
        city="Moscow",
        organizer="Organizer",
        course="50",
        status="ACTIVE",
        links=[],
        start_date=date(2026, 7, 30),
        end_date=date(2026, 7, 30),
    )


async def _create_athlete(index: int) -> Athlete:
    return await Athlete.create(
        last_name=f"Last{index}",
        first_name=f"First{index}",
        birth_year="2008",
        gender="M",
    )


def test_transfer_results_moves_relay_legs_and_allows_source_delete():
    async def scenario():
        await Tortoise.init(
            db_url="sqlite://:memory:",
            modules={"models": ["app.models"]},
        )
        await Tortoise.generate_schemas()
        try:
            competition = await _create_competition()
            source = await _create_athlete(1)
            target = await _create_athlete(2)

            relay_result = await RelayResult.create(
                competition=competition,
                name="Team",
                stroke="SURFACE",
                distance=50,
                relay_count=2,
                gender="M",
                result=None,
                status="COMPLETED",
            )
            relay_leg = await RelayLeg.create(
                relay_result=relay_result,
                athlete=source,
                order=1,
                result=None,
            )

            dry_run = await transfer_results(
                from_athlete_id=source.id,
                to_athlete_id=target.id,
                competition_id=competition.id,
            )
            assert dry_run.affected == 1
            assert dry_run.individual_results == 0
            assert dry_run.relay_legs == 1
            assert await RelayLeg.filter(id=relay_leg.id, athlete_id=source.id).exists()

            applied = await transfer_results(
                from_athlete_id=source.id,
                to_athlete_id=target.id,
                competition_id=competition.id,
                apply=True,
                delete_empty_source=True,
            )
            assert applied.affected == 1
            assert applied.remaining_source_results == 0
            assert applied.remaining_source_relay_legs == 0
            assert applied.deleted_source_athlete is True
            assert await RelayLeg.filter(id=relay_leg.id, athlete_id=target.id).exists()
            assert not await Athlete.filter(id=source.id).exists()
        finally:
            await Tortoise.close_connections()
            await Tortoise._reset_apps()

    asyncio.run(scenario())


def test_clear_empty_athletes_keeps_athletes_with_relay_legs():
    async def scenario():
        await Tortoise.init(
            db_url="sqlite://:memory:",
            modules={"models": ["app.models"]},
        )
        await Tortoise.generate_schemas()
        try:
            competition = await _create_competition()
            relay_athlete = await _create_athlete(1)
            result_athlete = await _create_athlete(2)
            empty_athlete = await _create_athlete(3)

            relay_result = await RelayResult.create(
                competition=competition,
                name="Team",
                stroke="SURFACE",
                distance=50,
                relay_count=2,
                gender="M",
            )
            await RelayLeg.create(
                relay_result=relay_result,
                athlete=relay_athlete,
                order=1,
            )
            await Result.create(
                athlete=result_athlete,
                competition=competition,
                stroke="SURFACE",
                distance=100,
                result=None,
            )

            dry_run = await clear_empty_athletes()
            assert dry_run.affected == 1

            applied = await clear_empty_athletes(apply=True)
            assert applied.affected == 1
            assert await Athlete.filter(id=relay_athlete.id).exists()
            assert await Athlete.filter(id=result_athlete.id).exists()
            assert not await Athlete.filter(id=empty_athlete.id).exists()
        finally:
            await Tortoise.close_connections()
            await Tortoise._reset_apps()

    asyncio.run(scenario())


def test_clear_results_removes_individual_and_relay_results():
    async def scenario():
        await Tortoise.init(
            db_url="sqlite://:memory:",
            modules={"models": ["app.models"]},
        )
        await Tortoise.generate_schemas()
        try:
            competition = await _create_competition()
            athlete = await _create_athlete(1)
            relay_result = await RelayResult.create(
                competition=competition,
                name="Team",
                stroke="SURFACE",
                distance=50,
                relay_count=2,
                gender="M",
            )
            await RelayLeg.create(
                relay_result=relay_result,
                athlete=athlete,
                order=1,
            )
            await Result.create(
                athlete=athlete,
                competition=competition,
                stroke="SURFACE",
                distance=100,
                result=None,
            )

            dry_run = await clear_results(competition.id)
            assert dry_run.affected == 2
            assert await Result.filter(competition_id=competition.id).count() == 1
            assert await RelayResult.filter(competition_id=competition.id).count() == 1

            applied = await clear_results(competition.id, apply=True)
            assert applied.affected == 2
            assert await Result.filter(competition_id=competition.id).count() == 0
            assert await RelayResult.filter(competition_id=competition.id).count() == 0
            assert await RelayLeg.all().count() == 0
        finally:
            await Tortoise.close_connections()
            await Tortoise._reset_apps()

    asyncio.run(scenario())


def test_athlete_detail_counts_relay_competitions_and_places():
    async def scenario():
        await Tortoise.init(
            db_url="sqlite://:memory:",
            modules={"models": ["app.models"]},
        )
        await Tortoise.generate_schemas()
        try:
            route_module = _load_athlete_route_module()
            competition = await _create_competition()
            athlete = await _create_athlete(1)
            relay_result = await RelayResult.create(
                competition=competition,
                name="Team",
                stroke="SURFACE",
                distance=50,
                relay_count=2,
                gender="M",
                place="1",
            )
            await RelayLeg.create(
                relay_result=relay_result,
                athlete=athlete,
                order=1,
            )

            response = await route_module.get_athlete(athlete.id)
            assert response.competitions_count == 1
            assert response.occupied_places_count == 1
        finally:
            await Tortoise.close_connections()
            await Tortoise._reset_apps()

    asyncio.run(scenario())
