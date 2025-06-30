from fastapi import APIRouter

from app.core.security.token import create_access_token, create_refresh_token
from app.schemas.auth.auth import TokenResponse, UserCreate
from app.shared.utils.registration import get_registration_handler

router = APIRouter()


@router.post("/", response_model=TokenResponse)
async def register_user(user_create: UserCreate):
    handler = get_registration_handler(user_create)
    user = await handler.register_user()

    refresh_token = create_refresh_token(user.id)
    access_token = create_access_token(user.id, fresh=True)

    return {
        "refresh_token": refresh_token,
        "access_token": access_token,
        "token_type": "Bearer",
    }
