
from datetime import datetime

from fastapi import APIRouter, Body

from app.core.errors import APIError, ErrorCode
from app.core.security.hashing import hash_password
from app.models.user.user import User
from app.models.user.user_verification import UserVerification
from app.shared.enums.enums import VerificationTokenEnum

router = APIRouter()


@router.get("/", status_code=204)
async def verified_token_password(
    user_id: int,
    token: str,
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
        raise APIError(ErrorCode.INVALID_VERIFICATION_CODE)


@router.post("/", status_code=204)
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
