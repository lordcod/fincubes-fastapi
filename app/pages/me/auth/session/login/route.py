from datetime import timedelta
from fastapi import APIRouter, Request, Response
from jwtifypy import JWTManager

from app.core.errors import APIError, ErrorCode
from app.core.security.hashing import verify_password
from app.integrations.cloudflare import check_verification
from app.models.user.user import User
from app.schemas.auth.auth import TokenResponse, UserLogin

router = APIRouter()
EXPIRES_IN = int(timedelta(minutes=15).total_seconds())


@router.post("/", response_model=TokenResponse)
async def login_user(user_login: UserLogin, request: Request, response: Response):
    ts = await check_verification(user_login.cf_token)
    if not ts.success:
        raise APIError(ErrorCode.CAPTCHA_FAILED)

    user = await User.filter(email=user_login.email).first()
    if not user:
        raise APIError(ErrorCode.USER_NOT_FOUND)

    if not verify_password(user_login.password, user.hashed_password):
        raise APIError(ErrorCode.INCORRECT_CURRENT_PASSWORD)

    manager = JWTManager.with_issuer(request.url.path).with_audience("auth")
    refresh_token = manager.create_refresh_token(user.id)
    access_token = manager.create_access_token(
        user.id, fresh=True, expires_delta=10)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/me/auth/session",
        max_age=7 * 24 * 3600,
    )

    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": EXPIRES_IN
    }
