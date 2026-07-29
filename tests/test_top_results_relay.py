from datetime import date, datetime, time, timezone

from app.repositories.sa.top_results import build_top_results_query
from app.repositories.sa.utils import compile_query_with_literals
from app.schemas.results.top import parse_best_full_result
from app.shared.enums.enums import EventTypeEnum


def test_top_results_query_includes_only_first_relay_leg():
    sql = compile_query_with_literals(
        build_top_results_query(
            stroke="SURFACE",
            distance=50,
            gender="M",
        )
    )

    assert "UNION ALL" in sql
    assert "'RELAY' AS event_type" in sql
    assert 'relay_legs."order" = 1' in sql
    assert "relay_legs.result IS NOT NULL" in sql


def test_top_result_parser_preserves_relay_event_type():
    now = datetime(2026, 7, 29, tzinfo=timezone.utc)
    row = {
        "result_created_at": now,
        "result_updated_at": now,
        "result_id": 9001,
        "result_athlete_id": 101,
        "result_competition_id": 123,
        "result_stroke": "SURFACE",
        "result_distance": 50,
        "result_result": time(0, 0, 24, 100_000),
        "result_final": None,
        "result_resolved_time": time(0, 0, 24, 100_000),
        "result_place": "1",
        "result_final_rank": None,
        "result_points": "50",
        "result_record": None,
        "result_status": "COMPLETED",
        "result_metadata": "{}",
        "result_event_type": "RELAY",
        "athlete_created_at": now,
        "athlete_updated_at": now,
        "athlete_id": 101,
        "athlete_last_name": "Иванов",
        "athlete_first_name": "Иван",
        "athlete_birth_year": "2008",
        "athlete_club": "СШ ВВС",
        "athlete_city": "Москва",
        "athlete_license": None,
        "athlete_gender": "M",
        "athlete_avatar_url": None,
        "athlete_is_top": False,
        "competition_created_at": now,
        "competition_updated_at": now,
        "competition_id": 123,
        "competition_name": "Кубок",
        "competition_date": "29.07.2026",
        "competition_location": "Бассейн",
        "competition_city": "Москва",
        "competition_organizer": "Организатор",
        "competition_course": "50",
        "competition_status": "COMPLETED",
        "competition_links": [],
        "competition_start_date": date(2026, 7, 29),
        "competition_end_date": date(2026, 7, 30),
        "competition_last_processed_at": None,
        "row_num": 3,
    }

    parsed = parse_best_full_result(row)

    assert parsed.result.event_type == EventTypeEnum.RELAY
    assert parsed.result.id == 9001
    assert str(parsed.result.result) == "00:24,10"
    assert parsed.result.metadata == {}
    assert parsed.row_num == 3


def test_top_result_parser_defaults_to_individual():
    now = datetime(2026, 7, 29, tzinfo=timezone.utc)
    row = {
        "result_created_at": now,
        "result_updated_at": now,
        "result_id": 501,
        "result_stroke": "SURFACE",
        "result_distance": 100,
        "athlete_created_at": now,
        "athlete_updated_at": now,
        "athlete_id": 101,
        "athlete_last_name": "Иванов",
        "athlete_first_name": "Иван",
        "athlete_birth_year": "2008",
        "athlete_gender": "M",
        "competition_created_at": now,
        "competition_updated_at": now,
        "competition_id": 123,
        "competition_name": "Кубок",
        "competition_date": "29.07.2026",
        "competition_location": "Бассейн",
        "competition_organizer": "Организатор",
        "competition_links": [],
        "competition_start_date": date(2026, 7, 29),
        "competition_end_date": date(2026, 7, 30),
        "row_num": 1,
    }

    parsed = parse_best_full_result(row)

    assert parsed.result.event_type == EventTypeEnum.INDIVIDUAL
