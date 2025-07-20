from fastapi import APIRouter, Request

from app.core.errors import APIError, ErrorCode
from app.core.security.hashing import verify_password
from app.core.security.token import create_access_token, create_refresh_token
from app.integrations.cloudflare import check_verification
from app.models.user.user import User
from app.schemas.auth.auth import TokenResponse, UserLogin

router = APIRouter()


@router.post("/", response_model=TokenResponse)
async def login_user(user_login: UserLogin, request: Request):
    ts = await check_verification(user_login.cf_token)
    if not ts.success:
        raise APIError(ErrorCode.CAPTCHA_FAILED)

    user = await User.filter(email=user_login.email).first()
    if not user:
        raise APIError(ErrorCode.USER_NOT_FOUND)

    if not verify_password(user_login.password, user.hashed_password):
        raise APIError(ErrorCode.INCORRECT_CURRENT_PASSWORD)

    refresh_token = create_refresh_token(
        user.id,
        issuer=request.url.path,
        audience="auth",
    )
    access_token = create_access_token(
        user.id,
        fresh=True,
        issuer=request.url.path,
        audience="auth",
    )

    return {
        "refresh_token": refresh_token,
        "access_token": access_token,
        "token_type": "Bearer",
    }
