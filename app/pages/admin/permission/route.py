from collections import Counter
from typing import List
from fastapi import APIRouter, Body

from app.models.user.group import Group, GroupCollection
from app.models.user.user import User
from app.schemas.users.group import Group_Pydantic, GroupCollection_Pydantic, LuckPermCommand
from app.shared.utils.scopes.request import extract_scopes, require_scope

router = APIRouter(tags=['Admin/Permission'])


@router.get("/")
@require_scope("superuser:read")
async def get_luck_perms_config():
    permisions = await extract_scopes()
    groups = await Group.all()
    tracks = await GroupCollection.all()
    users = await User.all()
    return dict(
        permisions=permisions,
        groups=groups,
        tracks=tracks,
        users=users
    )


@router.put("/", status_code=204)
@require_scope("superuser:write")
async def update_luck_perms(data: List[LuckPermCommand]):
    models = {
        'group': Group,
        'track': GroupCollection,
        'user': User,
    }
    for cmd in data:
        model = models[cmd.model]
        payload = cmd.payload
        if cmd.type == 'create':
            payload.pop('id', None)
            await model.create(**payload)
            return

        instance = await model.get(id=payload['id'])
        if cmd.type == 'update':
            await instance.update_from_dict(payload)
        if cmd.type == 'delete':
            await instance.delete()
