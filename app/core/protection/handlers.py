from app.core.errors import APIError, ErrorCode
from app.core.deps.ratelimit import (
    REQUEST_RATE_LIMIT_COUNT,
    REQUEST_RATE_LIMIT_INTERVAL_SECONDS,
    enforce_rate_limit,
)
from app.core.protection.utils import jwk_thumbprint, verify_dpop
from app.shared.utils.middleware_manager import MiddlewareManager

import time
from typing import Dict, Any
from fastapi import Request
from jwtifypy import JWTManager
from jwt import PyJWTError


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
    await enforce_rate_limit(
        redis,
        name="request",
        key=thumb,
        interval=REQUEST_RATE_LIMIT_INTERVAL_SECONDS,
        count=REQUEST_RATE_LIMIT_COUNT,
    )


manager = MiddlewareManager()
manager.register(validate_token)
manager.register(check_fingerprint)
manager.register(validate_dpop)
manager.register(check_rate_limit)
