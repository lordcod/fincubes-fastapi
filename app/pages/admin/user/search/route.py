from fastapi import APIRouter, Depends

from app.core.security.deps.permissions import admin_required
from app.models.user.user import User

router = APIRouter()


@router.get("/", dependencies=[Depends(admin_required)])
async def search_users(q: str):
    if q.isdigit():
        users = User.filter(id=int(q)).all()
    else:
        users = User.filter(email__icontains=q).all()
    users = await users.prefetch_related("athlete")
    return users
