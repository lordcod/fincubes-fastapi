from fastapi import APIRouter, Request
from jwtifypy import JWTManager

from app.schemas.auth.auth import TokenResponse, UserCreate
from app.shared.utils.registration import get_registration_handler

router = APIRouter()


@router.post("/", response_model=TokenResponse)
async def register_user(user_create: UserCreate, request: Request):
    handler = get_registration_handler(user_create)
    user = await handler.register_user()

    manager = JWTManager.with_issuer(request.url.path).with_audience("auth")
    refresh_token = manager.create_refresh_token(user.id)
    access_token = manager.create_access_token(user.id, fresh=True)

    return {
        "refresh_token": refresh_token,
        "access_token": access_token,
        "token_type": "Bearer",
    }
