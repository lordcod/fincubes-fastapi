
from datetime import datetime
from typing import Generic, TypeVar
from fastapi.security.base import SecurityBase

from app.core.security.deps.base_auth import BaseAuthSecurity
from app.core.errors import APIError, ErrorCode
from app.core.security.deps.base_interfaces import CookieRefreshGetToken, UserResolveEntity
from app.core.security.schema import TokenType, RefreshSecurityModel
from app.models.tokens.refresh_tokens import RefreshToken
from app.models.tokens.sessions import Session
from app.models.user.user import User

T = TypeVar('T')


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
            raise APIError(ErrorCode.INVALID_TOKEN)

        if refresh.revoked_at:
            await self.revoke_session(refresh.session)
            raise APIError(ErrorCode.INVALID_TOKEN)

        return refresh

    async def revoke_session(self, session: Session):
        now = datetime.now()

        session.revoked_at = now
        await session.save()

        await RefreshToken.filter(session=session).update(revoked_at=now)


class UserRefreshTokenSecurity(RefreshAuthSecurity[User], UserResolveEntity):
    pass
