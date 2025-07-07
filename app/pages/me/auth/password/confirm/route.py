
import secrets
import string
from datetime import datetime, timedelta

from fastapi import APIRouter, Body, Depends

from app.core.deps.ratelimit import create_ratelimit
from app.core.errors import APIError, ErrorCode
from app.integrations.mail import send_reset_password
from app.models.user.user import User
from app.models.user.user_verification import UserVerification
from app.shared.enums.enums import VerificationTokenEnum

router = APIRouter()

characters = string.ascii_letters + string.digits + "0123456789"
VERIFICATION_DELTA = timedelta(hours=1)
MIN_TIME_BETWEEN_CODES = 10 * 60


@router.post("/", status_code=204)
async def request_reset_password(
    email: str = Body(embed=True),
    send_limit=Depends(create_ratelimit(
        "reset_password:request", MIN_TIME_BETWEEN_CODES)),
):
    user = await User.filter(email=email).first()
    if not user:
        raise APIError(ErrorCode.USER_NOT_FOUND)

    # await send_limit(user.id)

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
