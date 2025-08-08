from re import A
from typing import List
from fastapi import APIRouter
from app.models.user.user import User
from app.schemas.auth.auth import UserResponse
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.get("/",  response_model=List[UserResponse])
@require_scope('user:read')
async def search_users(q: str):
    if q.isdigit():
        users = User.filter(id=int(q)).all()
    else:
        users = User.filter(email__icontains=q).all()
    return await users
