from datetime import timedelta
from fastapi import APIRouter, Request
from app.core.errors import APIError, ErrorCode
from app.core.security.deps.user_auth import UserAuthSecurity
from app.core.security.schema import TokenType
from app.schemas.auth.protection import ProtectionRequest
from app.shared.clients.redis import client
from app.core.protection.utils import verify_pow, verify_dpop, jwk_thumbprint
from jwtifypy import JWTManager

router = APIRouter()


@router.post("/")
async def issue_token(
    data: ProtectionRequest,
    request: Request
):
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

    try:
        user = await UserAuthSecurity(TokenType.access)(request)
    except Exception:
        user = None

    subject = user.id if user else 'anon'
    token = (
        JWTManager
        .with_issuer(request.url.path)
        .with_audience("public-system-verification")
        .create_token(
            subject=subject,
            token_type=TokenType.service,
            expires_delta=timedelta(minutes=2),
            cnf={"jkt": thumbprint, "jwk": data.jwk},
            fp=data.fingerprint,
            scopes=["*"],
        ))
    return {"token": token}
