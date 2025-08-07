from typing import Callable, Dict, Final, List, Optional, Set, cast
from fastapi import Depends, Request


ALL_SCOPES: Final[List[Callable]] = []


def require_scope(scope: str):
    if not isinstance(scope, str):
        raise TypeError

    def decorator(func):
        setattr(func, "required_scope", scope)
        ALL_SCOPES.append(func)
        return func
    return decorator


def get_all_scopes() -> List[Dict]:
    ret = []
    for func in ALL_SCOPES:
        scope = getattr(func, "required_scope", None)
        if scope is None:
            continue
        description = ' '.join(func.__name__.split('_')).title()
        ret.append({
            'node': scope,
            'description': description
        })
    return ret
