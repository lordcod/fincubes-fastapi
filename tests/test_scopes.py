import pytest
from app.shared.utils.scopes.combine import combine_all_scopes, flatten_scopes


def make_scope(node: str):
    if node.startswith('-'):
        node = node[1:]
        value = False
    else:
        value = True
    return {"node": node, "value": value, "inherited": None}


def make_role_scopes(scopes_list):
    return [make_scope(node) for node in scopes_list]


def test_full_scope_merge():
    default_scopes = make_role_scopes(["-*", "user:read", "posts:create"])
    roles = {
        "admin": {
            "rank": 100,
            "scopes": make_role_scopes(["user"]),
            "inherits": []
        },
        "mod": {
            "rank": 10,
            "scopes": make_role_scopes(["-user:write"]),
            "inherits": []
        },
        "supermod": {
            "rank": 50,
            "scopes":  make_role_scopes(["@mod", "posts:delete"]),
            "inherits": ["mod"]
        }
    }
    user_scopes = make_role_scopes(["-user:add", "@supermod", "@admin"])
    result = combine_all_scopes(roles, default_scopes, user_scopes)
    flattened = flatten_scopes(result)

    expected = [
        "posts:create,delete",
        "user:*,-add"
    ]
    assert sorted(flattened) == sorted(expected)


def test_wildcard_block_override():
    default_scopes = make_role_scopes(["*"])
    roles = {
        "reader": {
            "rank": 1,
            "scopes": make_role_scopes(["-*", "user:read", "admin:-*"]),
            "inherits": []
        }
    }
    user_scopes = make_role_scopes(["@reader"])

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
                    "scopes": make_role_scopes(["-user:read"]),
                    "inherits": []
                },
                "high": {
                    "rank": 999,
                    "scopes": make_role_scopes(["user:read"]),
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
                    "scopes": make_role_scopes(["user:read"]),
                    "inherits": []
                },
                "high": {
                    "rank": 1000,
                    "scopes": make_role_scopes(["-user:read"]),
                    "inherits": []
                }
            },
            ["low", "high"],
            ["user:-read"]
        )
    ]
)
def test_priority_resolution(roles, user_roles, expected):
    result = combine_all_scopes(roles, [], make_role_scopes(
        [f'@{role}' for role in user_roles]))
    flattened = flatten_scopes(result)
    assert sorted(flattened) == sorted(expected)


def test_user_scope_priority_over_role():
    roles = {
        "admin": {
            "rank": 50,
            "scopes": make_role_scopes(["user:*"]),
            "inherits": []
        }
    }
    result = combine_all_scopes(
        roles, [], make_role_scopes(["-user:write", "@admin"]))
    flattened = flatten_scopes(result)

    expected = ["user:*,-write"]
    assert sorted(flattened) == sorted(expected)


def test_default_scope():
    roles = {
        "default": {
            "rank": 0,
            "scopes": make_role_scopes(["user:*"]),
            "inherits": []
        }
    }
    result = combine_all_scopes(
        roles, make_role_scopes(["@default", "-user:read"]), [])
    flattened = flatten_scopes(result)

    expected = ['user:*,-read']
    assert sorted(flattened) == sorted(expected)


def test_user_scope():
    roles = {
        "user": {
            "rank": 0,
            "scopes": make_role_scopes(["user:*"]),
            "inherits": []
        }
    }
    result = combine_all_scopes(roles, make_role_scopes(
        ["-user:read"]), make_role_scopes(["@user"]))
    flattened = flatten_scopes(result)

    expected = ['user:*']
    assert sorted(flattened) == sorted(expected)


def test_inherited_user():
    result = combine_all_scopes(
        {},
        [],
        [{"node": "user:read", "value": True, "inherited": 0}]
    )
    flattened = flatten_scopes(result)
    assert sorted(flattened) == sorted([])


def test_inherited_user_roles():
    result = combine_all_scopes(
        {
            "test": {
                "rank": 100,
                "scopes": [
                    {"node": "user:read", "value": True, "inherited": None}
                ],
                "inherits": []
            }
        },
        [],
        [{"node": "@test", "value": True, "inherited": 0}]
    )
    flattened = flatten_scopes(result)
    assert sorted(flattened) == sorted([])


def test_inherited_role():
    result = combine_all_scopes(
        {
            "test": {
                "rank": 100,
                "scopes": [
                    {"node": "user:read", "value": True, "inherited": 0}
                ],
                "inherits": []
            }
        },
        [],
        [{"node": "@test", "value": True, "inherited": None}]
    )
    flattened = flatten_scopes(result)
    assert sorted(flattened) == sorted([])


def test_inherited_default():
    result = combine_all_scopes(
        {},
        [{"node": "user:read", "value": True, "inherited": 0}],
        []
    )
    flattened = flatten_scopes(result)
    assert sorted(flattened) == sorted([])


def test_inherited_default_role_check():
    result = combine_all_scopes(
        {
            "test": {
                "rank": 100,
                "scopes": [
                    {"node": "user:read", "value": True, "inherited": 0}
                ],
                "inherits": []
            }
        },
        [{"node": "@test", "value": True, "inherited": None}],
        []
    )
    flattened = flatten_scopes(result)
    assert sorted(flattened) == sorted([])


def test_inherited_default_role():
    result = combine_all_scopes(
        {
            "test": {
                "rank": 100,
                "scopes": [
                    {"node": "user:read", "value": True, "inherited": None}
                ],
                "inherits": []
            }
        },
        [{"node": "@test", "value": True, "inherited": 0}],
        []
    )
    flattened = flatten_scopes(result)
    assert sorted(flattened) == sorted([])
