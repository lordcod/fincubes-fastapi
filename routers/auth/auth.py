from fastapi import APIRouter, Depends
from passlib.context import CryptContext

from auth.user.registration import get_registration_handler
from misc.cloudflare import check_verification
from misc.errors import APIError, ErrorCode
from misc.security import (
    TokenType,
    UserAuthSecurity,
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from models.models import User
from schemas.auth import TokenResponse, UserCreate, UserLogin

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/register", response_model=TokenResponse)
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


@router.post("/login", response_model=TokenResponse)
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


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    current_user: User = Depends(UserAuthSecurity(TokenType.refresh)),
):
    access_token = create_access_token(current_user.id, fresh=False)

    return {"refresh_token": None, "access_token": access_token, "token_type": "Bearer"}


@router.put("/change-password", status_code=204)
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(UserAuthSecurity(TokenType.access)),
):
    if not verify_password(current_user.hashed_password, current_password):
        raise APIError(ErrorCode.INCORRECT_CURRENT_PASSWORD)

    hashed_new_password = hash_password(new_password)
    current_user.hashed_password = hashed_new_password
    await current_user.save()
