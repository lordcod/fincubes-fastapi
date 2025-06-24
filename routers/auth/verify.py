import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Body, Depends

from misc.errors import APIError, ErrorCode
from misc.mail import send_confirm_code
from misc.ratelimit import create_ratelimit
from misc.security import TokenType, UserAuthSecurity
from models.enums import VerificationTokenEnum
from models.models import User, UserVerification

router = APIRouter()
VERIFICATION_DELTA = timedelta(hours=1)
MIN_TIME_BETWEEN_CODES = 10 * 60


@router.post("/send-verify-code", status_code=204)
async def send_verify_code(
    current_user: User = Depends(UserAuthSecurity(TokenType.access)),
    send_limit=Depends(create_ratelimit(
        "verify_code", MIN_TIME_BETWEEN_CODES)),
):
    if current_user.verified:
        raise APIError(ErrorCode.ALREADY_VERIFIED)

    await send_limit(current_user.id)

    await UserVerification.filter(
        user_id=current_user.id,
        token_type=VerificationTokenEnum.VERIFY_EMAIL,
        is_active=True
    ).update(is_active=False)

    code = ''.join(secrets.choice("0123456789") for _ in range(6))
    today = datetime.now()
    await UserVerification.create(
        user=current_user,
        token=code,
        token_type=VerificationTokenEnum.VERIFY_EMAIL,
        token_expiry=today + VERIFICATION_DELTA
    )
    await send_confirm_code(current_user.email, code)


@router.post("/verify", status_code=204)
async def verify_email(
    code: str = Body(..., embed=True),
    current_user: User = Depends(UserAuthSecurity(TokenType.access)),
):
    if current_user.verified:
        raise APIError(ErrorCode.ALREADY_VERIFIED)

    today = datetime.now()
    verification = await UserVerification.filter(
        user_id=current_user.id,
        token_type=VerificationTokenEnum.VERIFY_EMAIL,
        is_active=True
    ).first()
    if verification is None:
        raise APIError(ErrorCode.VERIFICATION_NOT_FOUND)
    if verification.token_expiry.timestamp() < today.timestamp():
        raise APIError(ErrorCode.VERIFICATION_EXPIRED)

    if verification.token != code:
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

    current_user.verified = True
    await current_user.save()
