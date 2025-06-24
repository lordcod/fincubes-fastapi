import secrets
import string
from datetime import datetime, timedelta

from fastapi import APIRouter, Body, Depends
from passlib.context import CryptContext

from misc.errors import APIError, ErrorCode
from misc.mail import send_reset_password
from misc.ratelimit import create_ratelimit
from misc.security import (TokenType, UserAuthSecurity, hash_password,
                           verify_password)
from models.enums import VerificationTokenEnum
from models.models import User, UserVerification

router = APIRouter(tags=['password'])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
characters = string.ascii_letters + string.digits + "0123456789"

VERIFICATION_DELTA = timedelta(hours=1)
MIN_TIME_BETWEEN_CODES = 10 * 60


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


@router.post("/reset-password/request", status_code=204)
async def request_reset_password(
    email: str = Body(embed=True),
    send_limit=Depends(create_ratelimit(
        "reset_password:request", MIN_TIME_BETWEEN_CODES)),
):
    user = await User.filter(email=email).first()
    if not user:
        raise APIError(ErrorCode.USER_NOT_FOUND)

    await send_limit(user.id)

    await UserVerification.filter(
        user_id=user.id,
        token_type=VerificationTokenEnum.RESET_PASSWORD,
        is_active=True
    ).update(is_active=False)

    today = datetime.now()
    token = "".join(secrets.choice(characters) for i in range(128))
    await UserVerification.create(
        user=user,
        token=token,
        token_type=VerificationTokenEnum.RESET_PASSWORD,
        token_expiry=today + VERIFICATION_DELTA
    )
    await send_reset_password(user.email, user.id, token)


@router.post("/reset-password/confirm", status_code=204)
async def reset_password(
    user_id: int = Body(embed=True),
    token: str = Body(embed=True),
    password: str = Body(embed=True),
):
    user = await User.get_or_none(id=user_id)
    if not user:
        raise APIError(ErrorCode.USER_NOT_FOUND)

    today = datetime.now()
    verification = await UserVerification.filter(
        user_id=user_id,
        token_type=VerificationTokenEnum.RESET_PASSWORD,
        is_active=True
    ).first()
    if verification is None:
        raise APIError(ErrorCode.VERIFICATION_NOT_FOUND)
    if verification.token_expiry.timestamp() < today.timestamp():
        raise APIError(ErrorCode.VERIFICATION_EXPIRED)

    if verification.token != token:
        verification.attempt += 1
        error = None

        if verification.attempt >= 3:
            verification.is_active = False
            error = ErrorCode.VERIFICATION_ATTEMPTS_EXPIRED
        else:
            error = ErrorCode.INVALID_VERIFICATION_CODE

        await verification.save()
        raise APIError(error)

    verification.is_active = False
    await verification.save()

    user.hashed_password = hash_password(password)
    await user.save()
