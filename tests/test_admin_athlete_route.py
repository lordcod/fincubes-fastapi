import asyncio
import importlib.util
from pathlib import Path

from tortoise import Tortoise

from app.models import Athlete


def _load_admin_athlete_route_module():
    route_path = Path("app/pages/admin/athlete/route.py")
    spec = importlib.util.spec_from_file_location("admin_athlete_route", route_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_admin_athlete_search_with_limit_returns_serialized_athletes():
    async def scenario():
        await Tortoise.init(
            db_url="sqlite://:memory:",
            modules={"models": ["app.models"]},
        )
        await Tortoise.generate_schemas()
        try:
            route_module = _load_admin_athlete_route_module()
            athlete = await Athlete.create(
                last_name="Shamanova",
                first_name="Irina",
                birth_year="2019",
                gender="F",
            )

            response = await route_module.get_athletes_admin(
                last_name="Shamanova",
                first_name="Irina",
                birth_year=2019,
                gender="F",
                limit=10,
            )

            assert [item.id for item in response] == [athlete.id]
        finally:
            await Tortoise.close_connections()
            await Tortoise._reset_apps()

    asyncio.run(scenario())
