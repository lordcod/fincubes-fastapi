from datetime import datetime
from hashlib import md5
from typing import Generic, TypeVar
from urllib.parse import urlparse
from fastapi import Request
from fastapi.security.base import SecurityBase
from app.core.security.deps.base_auth import BaseAuthSecurity, BaseGetToken
from app.core.errors import APIError, ErrorCode
from app.core.security.deps.base_interfaces import UserResolveEntity
from app.core.security.schema import RefreshSecurityModel, TokenType
from app.models.tokens.refresh_tokens import RefreshToken
from app.models.tokens.sessions import Session
from app.models.user.user import User

T = TypeVar('T')


class CookieRefreshGetToken(BaseGetToken):
    async def get_token(self, request: Request) -> str:
        domain = urlparse(request.headers.get("origin")).hostname
        if isinstance(domain, bytes):
            domain = domain.decode()
        domain_b64 = md5(domain.encode()).hexdigest()

        token = (
            request.cookies.get(f"refresh_token_{domain_b64}")
            or request.cookies.get("refresh_token")
        )
        if not token:
            raise APIError(ErrorCode.INVALID_TOKEN, "отсутствует")
        return token


class RefreshAuthSecurity(Generic[T], SecurityBase, CookieRefreshGetToken, BaseAuthSecurity[T]):
    def __init__(self):
        super().__init__(TokenType.refresh)
        self.model = RefreshSecurityModel()
        self.scheme_name = self.__class__.__name__


class RefreshTokenSecurity(RefreshAuthSecurity[RefreshToken]):
    async def resolve_entity(self, payload: dict):
        refresh = await RefreshToken.get_or_none(id=payload['jti']).prefetch_related('session')

        # TODO DELETE 1 SEP
        if refresh is None:
            session = await Session.create(user_id=payload['sub'])
            refresh = await RefreshToken.create(
                id=payload['jti'],
                issued_at=payload['iat'],
                expires_at=payload['exp'],
                session=session,
            )
            return refresh

        if refresh.session.revoked_at:
            raise APIError(ErrorCode.INVALID_TOKEN, "session revoked")

        if refresh.revoked_at:
            await self.revoke_session(refresh.session)
            raise APIError(ErrorCode.INVALID_TOKEN, "refresh token revoked")

        return refresh

    async def revoke_session(self, session: Session):
        now = datetime.now()

        session.revoked_at = now
        await session.save()

        await RefreshToken.filter(session=session).update(revoked_at=now)


class UserRefreshTokenSecurity(RefreshAuthSecurity[User], UserResolveEntity):
    pass
