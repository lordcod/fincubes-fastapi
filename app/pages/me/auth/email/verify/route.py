
from datetime import datetime, timedelta

from fastapi import APIRouter, Body, Depends

from app.core.errors import APIError, ErrorCode
from app.core.security.auth import UserAuthSecurity
from app.core.security.schema import TokenType
from app.models.user.user import User
from app.models.user.user_verification import UserVerification
from app.shared.enums.enums import VerificationTokenEnum

router = APIRouter()
VERIFICATION_DELTA = timedelta(hours=1)
MIN_TIME_BETWEEN_CODES = 10 * 60


@router.post("/", status_code=204)
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
