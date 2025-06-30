from fastapi import APIRouter

from app.core.errors import APIError, ErrorCode
from app.core.security.token import create_access_token, create_refresh_token
from app.integrations.cloudflare import check_verification
from app.models.user.user import User
from app.schemas.auth.auth import TokenResponse, UserLogin

router = APIRouter()


@router.post("/", response_model=TokenResponse)
async def login_user(user_login: UserLogin):
    ts = await check_verification(user_login.cf_token)
    if not ts.success:
        raise APIError(ErrorCode.CAPTCHA_FAILED)

    user = await User.filter(email=user_login.email).first()
    if not user:
        raise APIError(ErrorCode.USER_NOT_FOUND)

    if not pwd_context.verify(user_login.password, user.hashed_password):
        raise APIError(ErrorCode.INCORRECT_CURRENT_PASSWORD)

    refresh_token = create_refresh_token(user.id)
    access_token = create_access_token(user.id, fresh=True)

    return {
        "refresh_token": refresh_token,
        "access_token": access_token,
        "token_type": "Bearer",
    }
