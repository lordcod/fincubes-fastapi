from collections import Counter
from typing import List
from fastapi import APIRouter

from app.models.user.group import Group, GroupCollection
from app.models.user.user import User
from app.schemas.users.group import Group_Pydantic, GroupCollection_Pydantic
from app.shared.clients.scopes.request import get_all_scopes

router = APIRouter(tags=['Admin/Permission'])


async def extract_scopes():
    already = set()
    categories = []
    new_scopes = [
        {'node': '*', 'description': 'Все разрешения'}
    ]
    scopes = get_all_scopes()
    for scope in scopes:
        node: str = scope['node']
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
                'description': f'Все разрешения {' '.join(category.split('_')).title()}'
            })
    return new_scopes


@router.get("/")
async def get_luck_perms_config():
    permisions = await extract_scopes()
    groups = await Group_Pydantic.from_queryset(Group.all())
    tracks = await GroupCollection_Pydantic.from_queryset(GroupCollection.all())
    users = await User.all()
    return dict(
        permisions=permisions,
        groups=groups,
        tracks=tracks,
        users=users
    )
