
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends

from app.core.deps.ratelimit import (
    EMAIL_CODE_RATE_LIMIT_COUNT,
    EMAIL_CODE_RATE_LIMIT_INTERVAL_SECONDS,
    create_ratelimit,
)
from app.core.errors import APIError, ErrorCode
from app.core.security.deps.user_auth import UserAuthSecurity
from app.integrations.mail import send_confirm_code
from app.models.user.user import User
from app.models.user.user_verification import UserVerification
from app.shared.enums.enums import VerificationTokenEnum

router = APIRouter()
VERIFICATION_DELTA = timedelta(hours=1)


@router.post("/", status_code=204)
async def send_verify_code(
    current_user: User = Depends(UserAuthSecurity()),
    send_limit=Depends(create_ratelimit(
        "verify_code",
        EMAIL_CODE_RATE_LIMIT_INTERVAL_SECONDS,
        count=EMAIL_CODE_RATE_LIMIT_COUNT,
    )),
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
