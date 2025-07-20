
import uuid
from fastapi import APIRouter, Header, Request
from app.core.errors import APIError, ErrorCode
from app.shared.clients.redis import client
from app.core.config import settings

router = APIRouter()


@router.get("/")
async def get_challenge(
    request: Request,
    x_fp: str = Header(default="nofp")
):
    ip = request.client.host

    if await client.incr(f"rl:challenge:{ip}:{x_fp}") > 30:
        raise APIError(ErrorCode.RATE_LIMIT_EXCEEDED)
    await client.expire(f"rl:challenge:{ip}:{x_fp}", 60)

    nonce = str(uuid.uuid4())
    await client.set(f"nonce:{nonce}", x_fp, ex=300)

    return {"server_nonce": nonce, "pow_bits": settings.POW_BITS}
