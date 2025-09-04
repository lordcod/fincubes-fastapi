from abc import ABC, abstractmethod
from datetime import timedelta
from urllib.parse import urlparse
from fastapi import APIRouter, Request, Response
from app.core.errors import APIError, ErrorCode
from app.integrations.captcha import check_verification
from app.models.user.user import User
from app.schemas.auth.auth import TokenResponse, UserLogin
from typing import Generic, TypeVar

from app.shared.utils.tokens import LoginTokenManager, TokenManager

T = TypeVar('T', bound='UserLogin')

router = APIRouter()
REFRESH_EXPIRES_IN = timedelta(days=31)
ACCESS_EXPIRES_IN = timedelta(minutes=15)
REFRESH_EXPIRES_IN_TOTAL = int(REFRESH_EXPIRES_IN.total_seconds())
ACCESS_EXPIRES_IN_TOTAL = int(ACCESS_EXPIRES_IN.total_seconds())


def get_response(access_token: str) -> TokenResponse:
    return TokenResponse(
        access_token=access_token,
        token_type="Bearer",
        expires_in=ACCESS_EXPIRES_IN_TOTAL
    )


class SetRefreshToken():
    def __init__(
        self,
        request: Request,
        response: Response
    ) -> None:
        self.request = request
        self.response = response

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


class BaseAuthRepository(ABC, SetRefreshToken):
    def __init__(
        self,
        request: Request,
        response: Response,
        token_manager: TokenManager,
    ) -> None:
        super().__init__(request, response)
        self.token_manager = token_manager

    async def run(self) -> TokenResponse:
        user = await self.get_user()
        refresh_token, access_token = await self.token_manager.extract_token(user)
        await self.set_refresh_token(refresh_token)
        return get_response(access_token)

    @abstractmethod
    async def get_user(self) -> User:
        ...


class AuthRepository(Generic[T], BaseAuthRepository):
    def __init__(
        self,
        user_login: T,
        request: Request,
        response: Response
    ) -> None:
        super().__init__(request, response, LoginTokenManager(request))
        self.user_login = user_login

    async def run(self) -> TokenResponse:
        await self.check_verification()
        return await super().run()

    async def check_verification(self):
        ts = await check_verification(self.user_login.cf_token)
        if not ts.success:
            raise APIError(ErrorCode.CAPTCHA_FAILED)
