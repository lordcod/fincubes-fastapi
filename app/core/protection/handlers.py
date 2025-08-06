
from app.core.config import settings
from app.core.errors import APIError, ErrorCode
from app.core.protection.utils import jwk_thumbprint, verify_dpop
from app.shared.utils.middleware_manager import MiddlewareManager

import time
from typing import Dict, Any
from fastapi import Request
from jose import jwt, JWTError


RATE_LIMIT = 60


async def validate_token(handler, event, data, x_page_token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(
            x_page_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={
                "verify_sub": False,
                "verify_aud": False,
                "verify_iss": False,
            },
        )
    except JWTError as exc:
        raise APIError(ErrorCode.PROTECTION_BAD_PAGE_TOKEN) from exc

    if payload.get("exp", 0) < int(time.time()):
        raise APIError(ErrorCode.PROTECTION_TOKEN_EXPIRED)

    data['payload'] = payload
    return await handler(event, data)


async def check_fingerprint(handler, event, data, payload: Dict[str, Any], x_fp: str):
    if x_fp != payload.get("fp"):
        raise APIError(ErrorCode.PROTECTION_FP_MISMATCH)
    return await handler(event, data)


async def validate_dpop(handler, request: Request, data, dpop: str, payload: Dict[str, Any]) -> str:
    jwk_pub = payload["cnf"]["jwk"]
    thumb = payload["cnf"]["jkt"]

    if jwk_thumbprint(jwk_pub) != thumb:
        raise APIError(ErrorCode.PROTECTION_JKT_MISMATCH)

    verify_dpop(request.method, str(request.url), dpop, jwk_pub)

    data['thumb'] = thumb
    return await handler(request, data)


async def check_rate_limit(handler, request: Request, data, thumb: str, redis):
    key = f"rl:req:{thumb}"
    if await redis.incr(key) > RATE_LIMIT:
        raise APIError(ErrorCode.RATE_LIMIT_EXCEEDED)
    await redis.expire(key, 60)
    return await handler(request, data)


manager = MiddlewareManager()
manager.register(validate_token)
manager.register(check_fingerprint)
manager.register(validate_dpop)
manager.register(check_rate_limit)
