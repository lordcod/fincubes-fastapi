import aiohttp
from os import getenv
from pydantic import BaseModel


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
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as response:
            result = await response.json()
            turnstile_result = TurnstileResponse(**result)
    return turnstile_result
