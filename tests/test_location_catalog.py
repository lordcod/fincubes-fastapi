import asyncio
from collections import defaultdict
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError
from tortoise import Tortoise

from app.core.errors import APIError, ErrorCode
from app.data.location_aliases import locations as legacy_locations
from app.models.location.location_alias import LocationAlias
from app.models.location.location_object import LocationObject
from app.pages.admin.locations.aliases.route import get_location_catalog
from app.schemas.location.location import (
    LocationAliasesAdd,
    LocationObjectCreate,
    LocationResolveRequest,
)
from app.services.location_catalog import (
    add_aliases_to_location_object,
    create_location_object,
    find_exact_alias,
    matches_required_location_context,
    normalize_location_text,
    resolve_athlete_location_fields,
    resolve_location_alias,
    search_location_entities,
)
from scripts.import_location_catalog import build_location_objects


def _objects_by_alias():
    objects, invalid = build_location_objects()
    by_alias = defaultdict(list)
    for item in objects:
        for alias in item["aliases"]:
            by_alias[alias].append(item)
    return objects, invalid, by_alias


def test_location_source_is_imported_without_semantic_ids():
    objects, invalid, by_alias = _objects_by_alias()

    assert len(legacy_locations) == 437
    assert objects
    assert invalid == []
    assert "Шатура г. Шатура" in by_alias
    assert all("club_id" not in item for item in objects)
    assert all("city_id" not in item for item in objects)
    assert all("region_id" not in item for item in objects)


def test_import_groups_aliases_by_textual_canonical_location():
    _, _, by_alias = _objects_by_alias()
    item = by_alias["Шатура г. Шатура"][0]

    assert item["club"] is None
    assert item["city"] == "Шатура"
    assert item["region"] == "Московская область"
    assert item["required"] == []


def test_multi_region_aliases_create_required_text_context_objects():
    _, _, by_alias = _objects_by_alias()
    variants = by_alias["СШ"]

    assert len(variants) >= 2
    assert all("region" in item["required"] for item in variants)
    assert len({item["region"] for item in variants}) == len(variants)


def test_location_normalization_is_case_whitespace_and_yo_insensitive():
    assert normalize_location_text("  МОСКВА  ") == "москва"
    assert normalize_location_text("Орёл") == normalize_location_text("орел")


def test_location_create_validation():
    with pytest.raises(ValidationError):
        LocationObjectCreate(aliases=["Команда"], region=" ")

    payload = LocationObjectCreate(
        aliases=[" Команда ", "КОМАНДА"],
        region=" Москва ",
    )
    assert payload.aliases == ["Команда", "КОМАНДА"]
    assert payload.region == "Москва"

    with pytest.raises(ValidationError):
        LocationAliasesAdd(aliases=["Команда", "Команда"])


def test_exact_alias_requires_region_when_several_objects(monkeypatch):
    locations = [
        SimpleNamespace(
            id=uuid4(),
            club="СШ",
            city=None,
            region="Первый регион",
        ),
        SimpleNamespace(
            id=uuid4(),
            club="СШ",
            city=None,
            region="Второй регион",
        ),
    ]
    rows = [
        SimpleNamespace(alias="СШ", required=["region"], location_object=locations[0]),
        SimpleNamespace(alias="СШ", required=["region"], location_object=locations[1]),
    ]

    class FakeQuerySet:
        def prefetch_related(self, *_fields):
            return self

        def __await__(self):
            async def resolve():
                return rows

            return resolve().__await__()

    monkeypatch.setattr(LocationAlias, "filter", lambda **_kwargs: FakeQuerySet())

    with pytest.raises(APIError) as exc:
        asyncio.run(find_exact_alias("СШ"))
    assert exc.value.error_code == ErrorCode.LOCATION_REGION_REQUIRED.code

    result = asyncio.run(find_exact_alias("СШ", region="Второй регион"))
    assert result is locations[1]


def test_required_context_matching_rules():
    location = SimpleNamespace(
        required=["city", "region"],
        region="Москва",
        city="Зеленоград",
    )

    assert not matches_required_location_context(location, required=location.required)
    assert not matches_required_location_context(
        location, region="Москва", required=location.required
    )
    assert not matches_required_location_context(
        location, city="Зеленоград", required=location.required
    )
    assert matches_required_location_context(
        location,
        region="Москва",
        city="Зеленоград",
        required=location.required,
    )
    assert not matches_required_location_context(
        location,
        region="Москва",
        city="Москва",
        required=location.required,
    )

    location.required = []
    assert matches_required_location_context(location, region="Любой")


def test_catalog_always_returns_lists_and_filters_required_rows(monkeypatch):
    def row(*, alias, region, required):
        location = SimpleNamespace(
            id=uuid4(),
            club=alias,
            city=None,
            region=region,
        )
        return SimpleNamespace(
            id=uuid4(),
            alias=alias,
            required=required,
            location_object=location,
        )

    unrestricted = row(
        alias="Обычная команда",
        region="Первый регион",
        required=[],
    )
    first = row(
        alias="Общая команда",
        region="Первый регион",
        required=["region"],
    )
    second = row(
        alias="Общая команда",
        region="Второй регион",
        required=["region"],
    )

    class FakeQuerySet:
        def prefetch_related(self, *_fields):
            return self

        def order_by(self, *_fields):
            return self

        def __await__(self):
            async def resolve():
                return [unrestricted, first, second]

            return resolve().__await__()

    monkeypatch.setattr(LocationAlias, "all", lambda: FakeQuerySet())

    full = asyncio.run(get_location_catalog())
    assert len(full["Обычная команда"]) == 1
    assert len(full["Общая команда"]) == 2

    filtered = asyncio.run(get_location_catalog(region="Второй регион"))
    assert len(filtered["Обычная команда"]) == 1
    assert [item.id for item in filtered["Общая команда"]] == [second.location_object.id]


def test_create_resolve_and_flat_athlete_fields():
    async def scenario():
        await Tortoise.init(
            db_url="sqlite://:memory:",
            modules={"models": ["app.models.location"]},
        )
        await Tortoise.generate_schemas()
        try:
            first = await create_location_object(
                LocationObjectCreate(
                    aliases=["Общая команда"],
                    club="СШ",
                    city="Первый город",
                    region="Первый регион",
                    required={"region"},
                )
            )
            second = await create_location_object(
                LocationObjectCreate(
                    aliases=["Общая команда"],
                    club="СШ",
                    city="Второй город",
                    region="Второй регион",
                    required={"region"},
                )
            )

            with pytest.raises(APIError) as ambiguous:
                await find_exact_alias("Общая команда")
            assert ambiguous.value.error_code == ErrorCode.LOCATION_REGION_REQUIRED.code

            resolved = await resolve_location_alias(
                LocationResolveRequest(alias="Общая команда", region="Второй регион")
            )
            assert resolved is not None
            assert resolved.id == second.id
            assert resolved.club == "СШ"
            assert resolved.city == "Второй город"

            athlete_fields = await resolve_athlete_location_fields(
                alias="Общая команда",
                club="Что угодно",
                city=None,
                region="Второй регион",
            )
            assert athlete_fields == {
                "club": "СШ",
                "city": "Второй город",
                "region": "Второй регион",
            }

            assert first.id != second.id
        finally:
            await Tortoise.close_connections()

    asyncio.run(scenario())


def test_new_athlete_alias_is_added_to_matching_canonical_location():
    async def scenario():
        await Tortoise.init(
            db_url="sqlite://:memory:",
            modules={"models": ["app.models.location"]},
        )
        await Tortoise.generate_schemas()
        try:
            location = await create_location_object(
                LocationObjectCreate(
                    aliases=["Старый alias"],
                    club="СШ",
                    city="Город",
                    region="Регион",
                )
            )

            fields = await resolve_athlete_location_fields(
                alias="Новый alias",
                club="СШ",
                city="Город",
                region="Регион",
            )
            await location.refresh_from_db()

            assert fields == {
                "club": "СШ",
                "city": "Город",
                "region": "Регион",
            }
            aliases = await LocationAlias.filter(location_object=location).order_by("alias")
            assert [alias.alias for alias in aliases] == ["Новый alias", "Старый alias"]
            assert await LocationObject.all().count() == 1
        finally:
            await Tortoise.close_connections()

    asyncio.run(scenario())


def test_add_aliases_updates_existing_object_idempotently():
    async def scenario():
        await Tortoise.init(
            db_url="sqlite://:memory:",
            modules={"models": ["app.models.location"]},
        )
        await Tortoise.generate_schemas()
        try:
            first = await create_location_object(
                LocationObjectCreate(
                    aliases=["Первая команда"],
                    club="Общая школа",
                    city="Первый город",
                    region="Первый регион",
                    required={"region"},
                )
            )
            second = await create_location_object(
                LocationObjectCreate(
                    aliases=["Вторая команда"],
                    club="Общая школа",
                    city="Второй город",
                    region="Второй регион",
                    required={"region"},
                )
            )

            await add_aliases_to_location_object(first.id, ["Новый alias"], ["region"])
            first_aliases = await LocationAlias.filter(location_object=first).order_by("alias")
            assert [alias.alias for alias in first_aliases] == ["Новый alias", "Первая команда"]

            await add_aliases_to_location_object(first.id, ["Новый alias"], ["region"])
            repeated_aliases = await LocationAlias.filter(
                location_object=first,
                alias="Новый alias",
            )
            assert len(repeated_aliases) == 1

            await add_aliases_to_location_object(second.id, ["Новый alias"], ["region"])
            second_aliases = await LocationAlias.filter(location_object=second)
            assert "Новый alias" in {alias.alias for alias in second_aliases}

            third = await create_location_object(
                LocationObjectCreate(
                    aliases=["Третья команда"],
                    club="Третья школа",
                    city="Третий город",
                    region="Третий регион",
                )
            )
            with pytest.raises(APIError) as conflict:
                await add_aliases_to_location_object(third.id, ["Новый alias"])
            assert conflict.value.error_code == ErrorCode.LOCATION_ALIAS_CONFLICT.code
        finally:
            await Tortoise.close_connections()

    asyncio.run(scenario())


def test_search_filters_by_required_text_context(monkeypatch):
    first_location = SimpleNamespace(
        id=uuid4(),
        club="СШ",
        city="Первый город",
        region="Первый регион",
    )
    second_location = SimpleNamespace(
        id=uuid4(),
        club="СШ",
        city="Второй город",
        region="Второй регион",
    )
    rows = [
        SimpleNamespace(
            id=uuid4(),
            alias="Общая команда",
            required=["region"],
            location_object=first_location,
        ),
        SimpleNamespace(
            id=uuid4(),
            alias="Общая команда",
            required=["region"],
            location_object=second_location,
        ),
    ]

    class FakeQuerySet:
        def prefetch_related(self, *_fields):
            return self

        def __await__(self):
            async def resolve():
                return rows

            return resolve().__await__()

    monkeypatch.setattr(LocationAlias, "all", lambda: FakeQuerySet())

    results = asyncio.run(
        search_location_entities("alias", "общая", region="Второй регион")
    )

    assert len(results) == 1
    assert results[0].id == second_location.id
    assert results[0].name == "Общая команда"
