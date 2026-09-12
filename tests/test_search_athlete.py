from app.repositories.sa.search_athlete import build_athlete_search_query
from app.repositories.sa.utils import compile_query_with_dollar_params


def _compile(query: str):
    statement = build_athlete_search_query(query, 15)
    return compile_query_with_dollar_params(statement)


def test_search_supports_partial_two_word_names():
    sql, params = _compile("аникин да")

    assert "ILIKE" in sql
    assert "%аникин%" in params
    assert "%да%" in params
    assert "similarity" not in sql


def test_search_supports_more_than_two_tokens():
    sql, params = _compile("аникин данил сергеевич")

    assert sql.count("ILIKE") >= 3
    assert "%аникин%" in params
    assert "%данил%" in params
    assert "%сергеевич%" in params


def test_short_search_is_always_empty():
    sql, params = _compile("ан")

    assert "LIMIT $1" in sql
    assert params == [0]
