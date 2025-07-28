from datetime import timedelta
from urllib.parse import urlparse
from fastapi import APIRouter, Request, Response
from jwtifypy import JWTManager

from app.schemas.auth.auth import TokenResponse, UserCreate
from app.shared.utils.registration import get_registration_handler

router = APIRouter()
EXPIRES_IN = int(timedelta(minutes=15).total_seconds())


@router.post("/", response_model=TokenResponse)
async def register_user(user_create: UserCreate, request: Request, response: Response):
    handler = get_registration_handler(user_create)
    user = await handler.register_user()

    manager = JWTManager.with_issuer(request.url.path).with_audience("auth")
    refresh_token = manager.create_refresh_token(user.id)
    access_token = manager.create_access_token(user.id, fresh=True)

    domain = urlparse(request.headers.get("origin")).hostname
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=7 * 24 * 3600,
        domain=domain
    )

    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": EXPIRES_IN
    }
