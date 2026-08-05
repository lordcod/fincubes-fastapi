
import uuid
from fastapi import APIRouter, Header, Request
from app.core.deps.ratelimit import (
    CHALLENGE_RATE_LIMIT_COUNT,
    CHALLENGE_RATE_LIMIT_INTERVAL_SECONDS,
    enforce_rate_limit,
)
from app.shared.clients.redis import client
from app.core.config import settings

router = APIRouter()


@router.get("/")
async def get_challenge(
    request: Request,
    x_fp: str = Header(default="nofp")
):
    ip = request.client.host

    await enforce_rate_limit(
        client,
        name="challenge",
        key=f"{ip}:{x_fp}",
        interval=CHALLENGE_RATE_LIMIT_INTERVAL_SECONDS,
        count=CHALLENGE_RATE_LIMIT_COUNT,
    )

    nonce = str(uuid.uuid4())
    await client.set(f"nonce:{nonce}", x_fp, ex=300)

    return {"server_nonce": nonce, "pow_bits": settings.POW_BITS}
