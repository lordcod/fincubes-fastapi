from pydantic import BaseModel
from typing import Optional

from app.core.config import settings
from app.shared.clients import session


class CaptchaResponse(BaseModel):
    status: str
    message: Optional[str] = None
    host: Optional[str] = None


async def check_verification(ip: str, token: str) -> CaptchaResponse:
    url = "https://smartcaptcha.yandexcloud.net/validate"
    data = {
        "secret": settings.CAPTCHA_SECRET_KEY,
        "token": token,
        "ip": ip
    }

    async with session.session.get(url, params=data) as response:
        result = await response.json()
        hcaptcha_result = CaptchaResponse(**result)

    return hcaptcha_result
