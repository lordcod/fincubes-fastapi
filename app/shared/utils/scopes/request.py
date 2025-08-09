from typing import Counter, Final, Optional, Set, cast
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


async def extract_scopes():
    already = set()
    categories = []
    new_scopes = [
        {'node': '*', 'description': 'Все разрешения'}
    ]
    for index, node in enumerate(ALL_SCOPES):
        scope = {"node": node, "id": index}
        category, _, _ = node.partition(':')
        categories.append(category)

        if node not in already:
            new_scopes.append(scope)
            already.add(node)
        else:
            part_scope = next(part_scope for part_scope in new_scopes
                              if part_scope['node'] == node)
            part_scope['description'] = f"{part_scope['description']}, {scope['description']}"

    for category, num in Counter(categories).items():
        if num == 1:
            continue
        if category not in already:
            new_scopes.append({
                'node': f'{category}:*',
                'description': f"Все разрешения {' '.join(category.split('_')).title()}",
                "id": new_scopes[-1].get('id', 0) + 1
            })

    return new_scopes
