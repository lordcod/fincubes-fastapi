from typing import Final, Set
from fastapi import Request


ALL_SCOPES: Final[Set[str]] = set()


def require_scope(scope: str):
    if not isinstance(scope, str):
        raise TypeError('')

    def decorator(func):
        setattr(func, "required_scope", scope)
        return func
    return decorator


async def get_scope_dependency(request: Request):
    route = request.scope.get("endpoint")
    required_scope = getattr(route, "required_scope", None)
    if required_scope and isinstance(required_scope, str):
        ALL_SCOPES.add(required_scope)
    return required_scope


def get_all_scopes() -> Set[str]:
    return ALL_SCOPES
