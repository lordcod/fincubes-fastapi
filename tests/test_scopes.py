import pytest
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
    user_scopes = ["-user:add", "@supermod", "@admin"]
    result = combine_all_scopes(roles, default_scopes, user_scopes)
    flattened = flatten_scopes(result)

    expected = [
        "posts:create,delete",
        "user:*,-add"
    ]
    assert sorted(flattened) == sorted(expected)


def test_wildcard_block_override():
    default_scopes = ["*"]
    roles = {
        "reader": {
            "rank": 1,
            "scopes": ["-*", "user:read", "admin:-*"],
            "inherits": []
        }
    }
    user_scopes = ["@reader"]

    result = combine_all_scopes(roles, default_scopes, user_scopes)
    flattened = flatten_scopes(result)

    expected = ["user:read"]
    assert sorted(flattened) == sorted(expected)


@pytest.mark.parametrize(
    "roles, user_roles, expected",
    [
        (
            {
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
            },
            ["low", "high"],
            ["user:read"]
        ),
        (
            {
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
            },
            ["low", "high"],
            ["user:-read"]
        )
    ]
)
def test_priority_resolution(roles, user_roles, expected):
    result = combine_all_scopes(roles, [], [f'@{role}' for role in user_roles])
    flattened = flatten_scopes(result)
    assert sorted(flattened) == sorted(expected)


def test_user_scope_priority_over_role():
    roles = {
        "admin": {
            "rank": 50,
            "scopes": ["user:*"],
            "inherits": []
        }
    }
    result = combine_all_scopes(roles, [], ["-user:write", "@admin"])
    flattened = flatten_scopes(result)

    expected = ["user:*,-write"]
    assert sorted(flattened) == sorted(expected)


def test_default_scope():
    roles = {
        "default": {
            "rank": 0,
            "scopes": ["user:*"],
            "inherits": []
        }
    }
    result = combine_all_scopes(roles, ["@default", "-user:read"], [])
    flattened = flatten_scopes(result)

    expected = ['user:*,-read']
    assert sorted(flattened) == sorted(expected)


def test_user_scope():
    roles = {
        "user": {
            "rank": 0,
            "scopes": ["user:*"],
            "inherits": []
        }
    }
    result = combine_all_scopes(roles, ["-user:read"], ["@user"])
    flattened = flatten_scopes(result)

    expected = ['user:*']
    assert sorted(flattened) == sorted(expected)
