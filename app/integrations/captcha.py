from pydantic import BaseModel, Field
from typing import List, Optional

from app.core.config import settings
from app.shared.clients import session


class HCaptchaResponse(BaseModel):
    success: bool
    challenge_ts: Optional[str] = None
    hostname: Optional[str] = None
    error_codes: Optional[List[str]] = Field(default=None, alias="error-codes")


async def check_verification(hcaptcha_token: str) -> HCaptchaResponse:
    url = "https://hcaptcha.com/siteverify"
    data = {
        "secret": settings.HCAPTCHA_SECRET_KEY,
        "response": hcaptcha_token,
    }

    async with session.session.post(url, data=data) as response:
        result = await response.json()
        hcaptcha_result = HCaptchaResponse(**result)

    return hcaptcha_result
