import asyncio
from collections import defaultdict
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from tortoise import Tortoise

from app.core.errors import APIError, ErrorCode
from app.data.location_aliases import locations as legacy_locations
from app.models.location.location_object import LocationObject
from app.pages.admin.locations.aliases.route import get_location_catalog
from app.schemas.location.location import (
    LocationAliasesAdd,
    LocationObjectCreate,
)
from app.services.location_catalog import (
    add_aliases_to_location_object,
    create_location_object,
    deterministic_entity_id,
    deterministic_location_object_id,
    find_exact_alias,
    matches_required_location_context,
    normalize_location_text,
    search_location_entities,
)
from scripts.import_location_catalog import build_location_objects


CRIMEA_ID = UUID("73941488-53f7-5fd2-bc1f-b61030bc7953")
SIMFEROPOL_ID = UUID("3f107a24-5586-5b0d-bcce-214bae523485")


def _objects_by_alias():
    objects, invalid = build_location_objects()
    by_alias = defaultdict(list)
    for item in objects:
        for alias in item["aliases"]:
            by_alias[alias].append(item)
    return objects, invalid, by_alias


def test_location_source_contains_reviewed_additions():
    objects, invalid, by_alias = _objects_by_alias()

    assert len(legacy_locations) == 437
    assert len(objects) == 508
    assert sum(len(item["aliases"]) for item in objects) == 772
    assert len(by_alias) == 764
    assert invalid == []
    assert all(
        "location_candidates" not in item
        for item in objects
    )


def test_reviewed_candidate_rules_are_applied():
    _, _, by_alias = _objects_by_alias()

    assert by_alias["Алтай Свим"][0]["city"] == "Горно-Алтайск"
    assert by_alias["Денисова О.Д."][0]["city"] == "Тула"
    assert by_alias["СТК Дельфин"][0]["city"] == "Озёрск"
    assert by_alias["Витязь"][0]["city"] == "Зеленогорск"
    assert by_alias["Витязь"][0]["region"] == "Красноярский край"
    assert by_alias["ПЦ Нептун"][0]["city"] == "Щёлково"
    assert by_alias['ШП "Нео Свим"'][0]["city"] == "Павловский Посад"


def test_multi_region_aliases_create_separate_required_objects():
    _, _, by_alias = _objects_by_alias()
    expected_counts = {
        'ГБУ ДО СО "СШОР ПО ВОДНЫМ ВИДАМ СПОРТА"': 2,
        "СШ": 3,
        "СШ ВВС": 2,
        "СШ Дельфин": 2,
        "СШОР": 2,
        "СШОР по ВВС": 2,
        "СШОР ЦВВС": 2,
    }

    for alias, count in expected_counts.items():
        assert len(by_alias[alias]) == count
        assert all(
            item["required"] == ["region"]
            for item in by_alias[alias]
        )
        assert len(
            {item["region_id"] for item in by_alias[alias]}
        ) == count


def test_original_ids_are_authoritative_for_additions():
    _, _, by_alias = _objects_by_alias()
    crimea_variant = next(
        item
        for item in by_alias["СШ ВВС"]
        if item["region"] == "Республика Крым"
    )

    assert crimea_variant["city"] == "Симферополь"
    assert crimea_variant["city_id"] == SIMFEROPOL_ID
    assert crimea_variant["region_id"] == CRIMEA_ID


def test_crimea_corrections_are_still_grouped():
    _, _, by_alias = _objects_by_alias()

    for alias in ('ГБУ ДО РК "СШ ВВС"', 'ГБУ ДО РК "СШ ВВС'):
        assert by_alias[alias][0]["city"] == "Симферополь"
        assert by_alias[alias][0]["city_id"] == SIMFEROPOL_ID
        assert by_alias[alias][0]["region_id"] == CRIMEA_ID

    assert by_alias["Группа Завдовьева"][0]["city"] is None
    assert by_alias["Группа Завдовьева"][0]["region_id"] == CRIMEA_ID

    mametov = by_alias["Маметов_TEAM"][0]
    assert mametov["club"] == "Маметов_TEAM"
    assert mametov["club_id"] == deterministic_entity_id(
        "club",
        "Маметов_TEAM",
    )
    assert mametov["city_id"] == SIMFEROPOL_ID


def test_location_normalization_is_case_whitespace_and_yo_insensitive():
    assert normalize_location_text("  МОСКВА  ") == "москва"
    assert normalize_location_text("Орёл") == normalize_location_text("орел")
    assert deterministic_location_object_id(
        uuid4(), None, CRIMEA_ID
    ) != deterministic_location_object_id(
        None, None, CRIMEA_ID
    )


def test_location_create_requires_region_and_consistent_optional_ids():
    with pytest.raises(ValidationError):
        LocationObjectCreate(aliases=["Команда"], region=" ")

    with pytest.raises(ValidationError):
        LocationObjectCreate(
            aliases=["Команда"],
            region="Москва",
            city_id=uuid4(),
        )

    payload = LocationObjectCreate(
        aliases=["Команда ", "КОМАНДА"],
        region=" Москва ",
    )
    assert payload.aliases == ["Команда ", "КОМАНДА"]
    assert payload.region == "Москва"

    with pytest.raises(ValidationError):
        LocationAliasesAdd(aliases=["Команда", "Команда"])


def test_exact_alias_requires_region_when_several_objects(monkeypatch):
    first_region_id = uuid4()
    second_region_id = uuid4()
    rows = [
        SimpleNamespace(
            aliases=["СШ"],
            region_id=first_region_id,
        ),
        SimpleNamespace(
            aliases=["СШ"],
            region_id=second_region_id,
        ),
    ]

    async def fake_all():
        return rows

    monkeypatch.setattr(LocationObject, "all", fake_all)

    with pytest.raises(APIError) as exc:
        asyncio.run(find_exact_alias("СШ"))
    assert exc.value.error_code == ErrorCode.LOCATION_REGION_REQUIRED.code

    result = asyncio.run(
        find_exact_alias("СШ", region_id=second_region_id)
    )
    assert result is rows[1]


def test_required_context_matching_rules():
    region_id = uuid4()
    city_id = uuid4()
    location = SimpleNamespace(
        required=["city", "region"],
        region_id=region_id,
        city_id=city_id,
    )

    assert matches_required_location_context(location)
    assert matches_required_location_context(
        location,
        region_id=region_id,
        city_id=city_id,
    )
    assert not matches_required_location_context(
        location,
        region_id=region_id,
    )
    assert not matches_required_location_context(
        location,
        city_id=city_id,
    )
    assert not matches_required_location_context(
        location,
        region_id=uuid4(),
        city_id=city_id,
    )

    location.required = []
    assert matches_required_location_context(
        location,
        region_id=uuid4(),
        city_id=uuid4(),
    )


def test_catalog_always_returns_lists_and_filters_required_rows(monkeypatch):
    first_region_id = uuid4()
    second_region_id = uuid4()

    def row(*, row_id, aliases, region_id, required):
        return SimpleNamespace(
            id=row_id,
            aliases=aliases,
            club=aliases[0],
            club_id=uuid4(),
            city=None,
            city_id=None,
            region=f"Регион {region_id}",
            region_id=region_id,
            required=required,
        )

    unrestricted = row(
        row_id=uuid4(),
        aliases=["Обычная команда"],
        region_id=first_region_id,
        required=[],
    )
    first = row(
        row_id=uuid4(),
        aliases=["Общая команда"],
        region_id=first_region_id,
        required=["region"],
    )
    second = row(
        row_id=uuid4(),
        aliases=["Общая команда"],
        region_id=second_region_id,
        required=["region"],
    )

    class FakeQuerySet:
        def order_by(self, *_fields):
            return self

        def __await__(self):
            async def resolve():
                return [unrestricted, first, second]

            return resolve().__await__()

    monkeypatch.setattr(LocationObject, "all", lambda: FakeQuerySet())

    full = asyncio.run(get_location_catalog())
    assert len(full["Обычная команда"]) == 1
    assert len(full["Общая команда"]) == 2

    filtered = asyncio.run(
        get_location_catalog(region_id=second_region_id)
    )
    assert len(filtered["Обычная команда"]) == 1
    assert [item.id for item in filtered["Общая команда"]] == [second.id]

    city_only = asyncio.run(get_location_catalog(city_id=uuid4()))
    assert "Общая команда" not in city_only
    assert len(city_only["Обычная команда"]) == 1


def test_create_allows_duplicate_alias_only_with_required_region():
    async def scenario():
        await Tortoise.init(
            db_url="sqlite://:memory:",
            modules={"models": ["app.models.location.location_object"]},
        )
        await Tortoise.generate_schemas()
        try:
            first = await create_location_object(
                LocationObjectCreate(
                    aliases=["Общая команда"],
                    club="Общая команда",
                    city="Первый город",
                    region="Первый регион",
                    required={"region"},
                )
            )
            second = await create_location_object(
                LocationObjectCreate(
                    aliases=["Общая команда"],
                    club="Общая команда",
                    city="Второй город",
                    region="Второй регион",
                    required={"region"},
                )
            )

            with pytest.raises(APIError) as ambiguous:
                await find_exact_alias("Общая команда")
            assert (
                ambiguous.value.error_code
                == ErrorCode.LOCATION_REGION_REQUIRED.code
            )
            assert (
                await find_exact_alias(
                    "Общая команда",
                    region_id=second.region_id,
                )
            ).id == second.id

            with pytest.raises(APIError) as conflict:
                await create_location_object(
                    LocationObjectCreate(
                        aliases=["Общая команда"],
                        club="Общая команда",
                        city="Третий город",
                        region="Третий регион",
                    )
                )
            assert (
                conflict.value.error_code
                == ErrorCode.LOCATION_ALIAS_CONFLICT.code
            )
            assert first.id != second.id
        finally:
            await Tortoise.close_connections()

    asyncio.run(scenario())


def test_add_aliases_updates_existing_object_idempotently():
    async def scenario():
        await Tortoise.init(
            db_url="sqlite://:memory:",
            modules={"models": ["app.models.location.location_object"]},
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

            updated = await add_aliases_to_location_object(
                first.id,
                ["Новый alias"],
            )
            assert updated.id == first.id
            assert updated.aliases == ["Первая команда", "Новый alias"]

            repeated = await add_aliases_to_location_object(
                first.id,
                ["Новый alias"],
            )
            assert repeated.aliases.count("Новый alias") == 1

            second_updated = await add_aliases_to_location_object(
                second.id,
                ["Новый alias"],
            )
            assert "Новый alias" in second_updated.aliases

            third = await create_location_object(
                LocationObjectCreate(
                    aliases=["Третья команда"],
                    club="Третья школа",
                    city="Третий город",
                    region="Третий регион",
                )
            )
            with pytest.raises(APIError) as conflict:
                await add_aliases_to_location_object(
                    third.id,
                    ["Новый alias"],
                )
            assert (
                conflict.value.error_code
                == ErrorCode.LOCATION_ALIAS_CONFLICT.code
            )

            with pytest.raises(APIError) as missing:
                await add_aliases_to_location_object(
                    uuid4(),
                    ["Alias"],
                )
            assert (
                missing.value.error_code
                == ErrorCode.LOCATION_OBJECT_NOT_FOUND.code
            )
        finally:
            await Tortoise.close_connections()

    asyncio.run(scenario())


def test_fuzzy_search_marks_only_normalized_exact_result(monkeypatch):
    class FakeConnection:
        async def execute_query_dict(self, sql, params):
            assert '"region"' in sql
            assert params[0] == "масква"
            return [
                {
                    "id": str(CRIMEA_ID),
                    "name": "Москва",
                    "similarity": 0.83,
                }
            ]

    monkeypatch.setattr(
        Tortoise,
        "get_connection",
        lambda _name: FakeConnection(),
    )

    results = asyncio.run(
        search_location_entities("region", "масква")
    )

    assert results[0].name == "Москва"
    assert results[0].exact_match is False
    assert results[0].similarity == 0.83
