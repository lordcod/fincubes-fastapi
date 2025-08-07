from datetime import datetime, timedelta
import uuid
from fastapi import Body, Request
from app.core.security.deps.base_auth import BaseAuthSecurity, BaseDecodeToken
from app.core.errors import APIError, ErrorCode
from app.core.security.schema import TokenType, RefreshSecurityModel
from fastapi.security.base import SecurityBase
from jwtifypy import JWTManager

from app.models.tokens.refresh_tokens import RefreshToken
from app.models.tokens.sessions import Session
from app.models.user.user import User

REFRESH_EXPIRES_IN = timedelta(days=31)
ACCESS_EXPIRES_IN = timedelta(minutes=15)
REFRESH_EXPIRES_IN_TOTAL = int(REFRESH_EXPIRES_IN.total_seconds())
ACCESS_EXPIRES_IN_TOTAL = int(ACCESS_EXPIRES_IN.total_seconds())


class RefreshTokenSecurity(SecurityBase, BaseDecodeToken):
    def __init__(self):
        super().__init__(TokenType.refresh)
        self.model = RefreshSecurityModel()
        self.scheme_name = self.__class__.__name__

    async def __call__(self, request: Request, session_id: str = Body(embed=True)):
        token = await self.get_token(request)
        payload = self.decode_token(token)

    async def get_token(self, request: Request) -> str:
        token = request.cookies.get("refresh_token")
        if not token:
            raise APIError(ErrorCode.INVALID_TOKEN)
        return token

    async def revoke_session(self, session: Session):
        now = datetime.now()

        session.revoked_at = now
        await session.save()

        await RefreshToken.filter(session=session).update(revoked_at=now)

    async def check_token(self, payload: dict, session_id: str):
        refresh = await RefreshToken.get(payload['jti']).prefetch_related('session')
        if refresh.session.id == session_id:
            await self.revoke_session(refresh.session)
            raise APIError(ErrorCode.INVALID_TOKEN)
        if refresh.session.revoked_at:
            raise APIError(ErrorCode.INVALID_TOKEN)
        if refresh.revoked_at:
            await self.revoke_session(refresh.session)
            raise APIError(ErrorCode.INVALID_TOKEN)

    async def generate_new_token(self, request: Request, user: User):
        manager = JWTManager.with_issuer(
            request.url.path).with_audience("auth")

        session_id = str(uuid.uuid4())
        refresh_id = str(uuid.uuid4())
        access_id = str(uuid.uuid4())
        now = datetime.now()

        session = await Session.create(id=session_id, user_id=user.id)
        await RefreshToken.create(
            id=refresh_id,
            access_id=access_id,
            session=session,
            issued_at=now,
            expires_at=now + REFRESH_EXPIRES_IN
        )

        refresh_token = manager.create_refresh_token(
            user.id,
            expires_delta=REFRESH_EXPIRES_IN,
            jti=refresh_id,
            session_id=session_id
        )
        access_token = manager.create_access_token(
            user.id,
            expires_delta=ACCESS_EXPIRES_IN,
            fresh=True,
            jti=access_id,
            session_id=session_id
        )

        return refresh_token, access_token, session_id
