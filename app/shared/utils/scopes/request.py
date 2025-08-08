from typing import Final, Optional, Set, cast
from fastapi import Depends, Request


ALL_SCOPES: Final[Set[str]] = set()


def require_scope(scope: str):
    if not isinstance(scope, str):
        raise TypeError('')
    ALL_SCOPES.add(scope)

    def decorator(func):
        setattr(func, "required_scope", scope)
        return func
    return decorator


def get_all_scopes() -> Set[str]:
    return ALL_SCOPES
