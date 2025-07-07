from fastapi import APIRouter, HTTPException, Request
from app.core.config import settings
from app.core.errors import APIError, ErrorCode
from app.schemas.auth.protection import ProtectionRequest
from app.shared.clients.redis import client
from app.core.protection.utils import verify_pow, verify_dpop, jwk_thumbprint
import time
from jose import jwt

router = APIRouter()


@router.post("/")
async def issue_token(data: ProtectionRequest, request: Request):
    ip = request.client.host

    if await client.incr(f"rl:token:{ip}:{data.fingerprint}") > 5:
        raise APIError(ErrorCode.RATE_LIMIT_EXCEEDED)
    await client.expire(f"rl:token:{ip}:{data.fingerprint}", 60)

    if not await client.delete(f"nonce:{data.server_nonce}"):
        raise APIError(ErrorCode.PROTECTION_NONCE_REUSED)

    verify_pow(data.server_nonce, data.nonce, data.fingerprint)
    verify_dpop(
        request.method,
        str(request.url),
        data.dpop,
        data.jwk
    )

    thumbprint = jwk_thumbprint(data.jwk)

    now = int(time.time())
    payload = {
        "sub": "anon",
        "iat": now,
        "exp": now + 120,
        "cnf": {"jkt": thumbprint, "jwk": data.jwk},
        "fp": data.fingerprint,
        "scopes": ["*"]
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return {"token": token}
