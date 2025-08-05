import math
from typing import Dict, Set, List

from app.shared.clients.scopes.combine import combine_all_scopes, flatten_scopes


def test_full_scope_merge():
    default_scopes = ["-*", "user:read", "posts:create"]
    roles = {
        "admin": {
            "rank": 100,
            "scopes": ["user"],
            "inherits": []
        },
        "mod": {
            "rank": 10,
            "scopes": ["-user:write"],
            "inherits": []
        },
        "supermod": {
            "rank": 50,
            "scopes": ["@mod", "posts:delete"],
            "inherits": ["mod"]
        }
    }
    user_scopes = ["-user:add"]
    user_roles = ["supermod", "admin"]

    # Твой вызов
    result = combine_all_scopes(default_scopes, roles, user_scopes, user_roles)
    flattened = flatten_scopes(result)

    # 🔍 Ожидаемый результат
    expected = [
        "posts:create,delete",
        "user:*,-add"
    ]

    assert sorted(flattened) == sorted(
        expected), f"Ожидалось {expected}, получено {flattened}"
    print("✅ Тест 1 пройден")


def test_wildcard_block_override():
    default_scopes = ["*"]
    roles = {
        "reader": {
            "rank": 1,
            "scopes": ["-*", "user:read", "admin:-*"],
            "inherits": []
        }
    }
    user_roles = ["reader"]
    user_scopes = []

    result = combine_all_scopes(default_scopes, roles, user_scopes, user_roles)
    flattened = flatten_scopes(result)

    expected = ["user:read"]
    assert sorted(flattened) == sorted(
        expected), f"Ожидалось {expected}, получено {flattened}"
    print("✅ Тест 2 пройден")


def test_high_priority_cancels_lower_negative():
    roles = {
        "low": {
            "rank": 1,
            "scopes": ["-user:read"],
            "inherits": []
        },
        "high": {
            "rank": 999,
            "scopes": ["user:read"],
            "inherits": []
        }
    }
    result = combine_all_scopes([], roles, [], ["low", "high"])
    flattened = flatten_scopes(result)

    expected = ["user:read"]
    assert sorted(flattened) == sorted(
        expected), f"Ожидалось {expected}, получено {flattened}"
    print("✅ Тест 3 пройден")


def test_negative_override_high_positive():
    roles = {
        "low": {
            "rank": 1,
            "scopes": ["user:read"],
            "inherits": []
        },
        "high": {
            "rank": 1000,
            "scopes": ["-user:read"],
            "inherits": []
        }
    }
    result = combine_all_scopes([], roles, [], ["low", "high"])
    flattened = flatten_scopes(result)

    expected = ["user:-read"]
    assert sorted(flattened) == sorted(
        expected), f"Ожидалось {expected}, получено {flattened}"
    print("✅ Тест 4 пройден")


def test_user_scope_priority_over_role():
    roles = {
        "admin": {
            "rank": 50,
            "scopes": ["user:*"],
            "inherits": []
        }
    }
    result = combine_all_scopes([], roles, ["-user:write"], ["admin"])
    flattened = flatten_scopes(result)

    expected = ["user:*,-write"]
    assert sorted(flattened) == sorted(
        expected), f"Ожидалось {expected}, получено {flattened}"
    print("✅ Тест 5 пройден")


def run_all_tests():
    test_full_scope_merge()
    test_wildcard_block_override()
    test_high_priority_cancels_lower_negative()
    test_negative_override_high_positive()
    test_user_scope_priority_over_role()


if __name__ == "__main__":
    run_all_tests()
