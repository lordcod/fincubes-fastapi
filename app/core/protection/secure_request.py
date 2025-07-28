import time
from typing import Dict, Any

from fastapi import Header, Request

from jose import jwt, JWTError

from app.core.config import settings
from app.shared.clients.redis import client
from app.core.errors import APIError, ErrorCode
from app.core.protection.utils import verify_dpop, jwk_thumbprint


class SecureRequest:
    """Depends‑валидатор Zero‑Trust с настраиваемыми правами."""

    RATE_LIMIT = 60  # req / minute per thumbprint

    async def __call__(
        self,
        request: Request,
        x_page_token: str = Header(alias="X-Page-Token"),
        dpop: str = Header(alias="DPoP"),
        x_fp: str = Header(alias="X-FP"),
    ) -> Dict[str, Any]:
        payload = self._parse_and_verify_token(x_page_token)
        self._check_fingerprint(payload, x_fp)
        thumb = self._check_dpop(request, dpop, payload)
        await self._rate_limit(thumb)
        self._check_scopes(payload)

        request.state.jwt = payload
        request.state.user = payload.get("sub", "anon")
        request.state.scope = set(payload.get("scopes", []))

        return payload

    def _parse_and_verify_token(self, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                options={"verify_sub": False,
                         "verify_aud": False,
                         "verify_iss": False},
            )
        except JWTError as exc:
            raise APIError(ErrorCode.PROTECTION_BAD_PAGE_TOKEN) from exc

        if payload["exp"] < int(time.time()):
            raise APIError(ErrorCode.PROTECTION_TOKEN_EXPIRED)

        return payload

    def _check_fingerprint(self, payload: Dict[str, Any], x_fp: str) -> None:
        if x_fp != payload.get("fp"):
            raise APIError(ErrorCode.PROTECTION_FP_MISMATCH)

    def _check_dpop(
        self, request: Request, dpop_jwt: str, payload: Dict[str, Any]
    ) -> str:
        jwk_pub = payload["cnf"]["jwk"]
        thumb = payload["cnf"]["jkt"]

        if jwk_thumbprint(jwk_pub) != thumb:
            raise APIError(ErrorCode.PROTECTION_JKT_MISMATCH)

        verify_dpop(
            request.method,
            str(request.url),
            dpop_jwt,
            jwk_pub
        )

        return thumb

    async def _rate_limit(self, thumb: str) -> None:
        key = f"rl:req:{thumb}"
        if await client.incr(key) > self.RATE_LIMIT:
            raise APIError(ErrorCode.RATE_LIMIT_EXCEEDED)
        await client.expire(key, 60)

    def _check_scopes(self, payload: Dict[str, Any]) -> None:
        token_scopes = set(payload.get("scopes", []))
        if "*" in token_scopes:
            return
        # if not self.required_scopes.issubset(token_scopes):
        #     raise APIError(ErrorCode.RATE_LIMIT_EXCEEDED)
