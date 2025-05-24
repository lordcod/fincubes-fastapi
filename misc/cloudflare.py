from os import getenv
from pydantic import BaseModel
from services import s3_session


TURNSTILE_SECRET_KEY = getenv('TURNSTILE_SECRET_KEY')


class TurnstileResponse(BaseModel):
    success: bool
    error_codes: list[str] = []


async def check_verification(turnstile_token: str) -> TurnstileResponse:
    url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    data = {
        "secret": TURNSTILE_SECRET_KEY,
        "response": turnstile_token
    }
    async with s3_session.session.post(url, data=data) as response:
        result = await response.json()
        turnstile_result = TurnstileResponse(**result)
    return turnstile_result
