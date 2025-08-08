from app.core.errors import APIError, ErrorCode
from app.core.protection.utils import jwk_thumbprint, verify_dpop
from app.shared.utils.middleware_manager import MiddlewareManager

import time
from typing import Dict, Any
from fastapi import Request
from jwtifypy import JWTManager
from jwt import PyJWTError


RATE_LIMIT = 60


async def validate_token(x_page_token: str) -> Dict[str, Any]:
    try:
        payload = JWTManager.decode_token(x_page_token)
    except PyJWTError as exc:
        raise APIError(ErrorCode.PROTECTION_BAD_PAGE_TOKEN) from exc

    if payload.get("exp", 0) < int(time.time()):
        raise APIError(ErrorCode.PROTECTION_TOKEN_EXPIRED)

    return {'payload': payload}


async def check_fingerprint(payload: Dict[str, Any], x_fp: str):
    if x_fp != payload.get("fp"):
        raise APIError(ErrorCode.PROTECTION_FP_MISMATCH)


async def validate_dpop(request: Request, dpop: str, payload: Dict[str, Any]):
    jwk_pub = payload["cnf"]["jwk"]
    thumb = payload["cnf"]["jkt"]

    if jwk_thumbprint(jwk_pub) != thumb:
        raise APIError(ErrorCode.PROTECTION_JKT_MISMATCH)

    verify_dpop(request.method, str(request.url), dpop, jwk_pub)

    return {
        'thumb': thumb
    }


async def check_rate_limit(thumb: str, redis):
    key = f"rl:req:{thumb}"
    if await redis.incr(key) > RATE_LIMIT:
        raise APIError(ErrorCode.RATE_LIMIT_EXCEEDED)
    await redis.expire(key, 60)


manager = MiddlewareManager()
manager.register(validate_token)
manager.register(check_fingerprint)
manager.register(validate_dpop)
manager.register(check_rate_limit)
