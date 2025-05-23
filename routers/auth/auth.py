from fastapi import APIRouter, Depends
from auth.user.registration import get_registration_handler
from misc.errors import APIError, ErrorCode
from models.models import User
from schemas.auth import UserCreate, UserLogin, TokenResponse
from passlib.context import CryptContext
from misc.security import get_current_user, hash_password, verify_password, create_access_token
from misc.cloudflare import check_verification


router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/register", response_model=TokenResponse)
async def register_user(user_create: UserCreate):
    handler = get_registration_handler(user_create)
    user = await handler.register_user()

    access_token = create_access_token(data={"sub": user.email})

    return {"access_token": access_token, "token_type": "Bearer"}


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

    access_token = create_access_token(data={"sub": user.email})

    return {"access_token": access_token, "token_type": "Bearer"}


@router.put("/change-password", status_code=204)
async def change_password(current_password: str, new_password: str, current_user: User = Depends(get_current_user)):
    if not verify_password(current_user.hashed_password, current_password):
        raise APIError(ErrorCode.INCORRECT_CURRENT_PASSWORD)

    hashed_new_password = hash_password(new_password)
    current_user.hashed_password = hashed_new_password
    await current_user.save()
