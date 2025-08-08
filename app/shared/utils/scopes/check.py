
from typing import Optional, List


def has_scope(scopes: List[str], scope_to_check: Optional[str] = None) -> bool:
    if scope_to_check is None:
        return True
    category_check, right_check = (scope_to_check.split(':', 1) + [None])[:2]

    scope = next(
        (s for s in scopes if s.startswith(f'{category_check}:')), None)
    if not scope:
        return '*' in scopes

    rights = scope[len(category_check)+1:].split(',')
    denied = {r[1:] for r in rights if r.startswith('-')}
    granted = {r for r in rights if not r.startswith('-')}

    if right_check in denied:
        return False
    if '*' in denied and right_check not in granted:
        return False

    return (
        '*' in scopes
        or '*' in granted
        or right_check in granted
    )
