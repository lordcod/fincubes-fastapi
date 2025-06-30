from os import getenv

from pydantic import BaseModel

from app.core.config import settings
from app.shared.clients import session


class TurnstileResponse(BaseModel):
    success: bool
    error_codes: list[str] = []


async def check_verification(turnstile_token: str) -> TurnstileResponse:
    url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    data = {"secret": settings.TURNSTILE_SECRET_KEY,
            "response": turnstile_token}
    async with session.session.post(url, data=data) as response:
        result = await response.json()
        turnstile_result = TurnstileResponse(**result)
    return turnstile_result
