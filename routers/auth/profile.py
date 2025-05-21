from fastapi import APIRouter, Depends
from models.models import User
from schemas.auth import UserResponse
from misc.security import get_current_user


router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def protected_endpoint(current_user: User = Depends(get_current_user)):
    return current_user
