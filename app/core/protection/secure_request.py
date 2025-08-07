from app.core.deps.redis import get_redis
from app.core.errors import APIError, ErrorCode
from app.core.security.deps.scope_auth import ScopeAuthSecurity

from typing import Optional
from fastapi import Depends, Header, Request
from .handlers import manager


async def handle(_):
    pass


class SecureRequest:
    """Zero-Trust Depends‑валидатор с декомпозицией на функции."""

    async def __call__(
        self,
        request: Request,
        is_scope_authorized: bool = ScopeAuthSecurity(auto_error=False),
        x_page_token: Optional[str] = Header(
            default=None, alias="X-Page-Token"),
        dpop: Optional[str] = Header(default=None, alias="DPoP"),
        x_fp: Optional[str] = Header(default=None, alias="X-FP"),
        redis=Depends(get_redis)
    ) -> None:
        if is_scope_authorized:
            return

        if None in {x_page_token, dpop, x_fp}:
            raise APIError(ErrorCode.PROTECTION_INVALID)

        await manager.run(handle, request, dict(
            x_page_token=x_page_token,
            dpop=dpop,
            x_fp=x_fp,
            redis=redis
        ))
