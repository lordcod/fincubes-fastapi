from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from urllib.parse import urlparse
import uuid
from fastapi import APIRouter, Request, Response
from jwtifypy import JWTManager

from app.core.errors import APIError, ErrorCode
from app.core.security.hashing import verify_password
from app.integrations.cloudflare import check_verification
from app.models.tokens.refresh_tokens import RefreshToken
from app.models.tokens.sessions import Session
from app.models.user.user import User
from app.schemas.auth.auth import TokenResponse, UserLogin
from typing import Generic, TypeVar

T = TypeVar('T', bound='UserLogin')

router = APIRouter()
REFRESH_EXPIRES_IN = timedelta(days=31)
ACCESS_EXPIRES_IN = timedelta(minutes=15)
REFRESH_EXPIRES_IN_TOTAL = int(REFRESH_EXPIRES_IN.total_seconds())
ACCESS_EXPIRES_IN_TOTAL = int(ACCESS_EXPIRES_IN.total_seconds())


class AuthRepository(ABC, Generic[T]):
    def __init__(
        self,
        user_login: T,
        request: Request,
        response: Response
    ) -> None:
        self.user_login = user_login
        self.request = request
        self.response = response

    async def run(self) -> TokenResponse:
        await self.check_verification()
        user = await self.get_user()
        refresh_token, access_token, session_id = await self.extract_token(user)
        await self.set_refresh_token(refresh_token)
        return await self.get_response(access_token, session_id)

    async def check_verification(self):
        ts = await check_verification(self.user_login.cf_token)
        if not ts.success:
            raise APIError(ErrorCode.CAPTCHA_FAILED)

    @abstractmethod
    async def get_user(self) -> User:
        ...

    async def extract_token(self, user: User):
        manager = JWTManager.with_issuer(
            self.request.url.path).with_audience("auth")

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

    async def set_refresh_token(self, refresh_token: str):
        domain = urlparse(self.request.headers.get("origin")).hostname
        if isinstance(domain, bytes):
            domain = domain.decode()

        self.response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="none",
            path="/me/auth/session",
            max_age=7 * 24 * 3600,
            domain=domain
        )

    async def get_response(self, access_token: str, session_id: uuid.UUID) -> TokenResponse:
        return TokenResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in=ACCESS_EXPIRES_IN_TOTAL,
            session_id=session_id
        )
