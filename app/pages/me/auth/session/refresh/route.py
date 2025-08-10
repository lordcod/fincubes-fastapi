from datetime import timedelta
from urllib.parse import urlparse
from fastapi import APIRouter, Body, Depends, Request, Response
from app.core.security.deps.refresh_auth import RefreshTokenSecurity, UserRefreshTokenSecurity
from app.models.tokens.refresh_tokens import RefreshToken
from app.models.user.user import User
from app.schemas.auth.auth import TokenResponse
from app.shared.utils.auth import BaseAuthRepository, SetRefreshToken
from app.shared.utils.token_manager import RefreshTokenManager, TokenManager

router = APIRouter()
REFRESH_EXPIRES_IN = timedelta(days=31)
ACCESS_EXPIRES_IN = timedelta(minutes=15)
REFRESH_EXPIRES_IN_TOTAL = int(REFRESH_EXPIRES_IN.total_seconds())
ACCESS_EXPIRES_IN_TOTAL = int(ACCESS_EXPIRES_IN.total_seconds())


class RefreshAuthRepository(BaseAuthRepository):
    def __init__(self, request: Request, response: Response, token_manager: TokenManager, user: User) -> None:
        super().__init__(request, response, token_manager)
        self.user = user

    async def get_user(self) -> User:
        return self.user


@router.post("/", response_model=TokenResponse)
async def post_refresh(
    request: Request,
    response: Response,
    refresh: RefreshToken = Depends(RefreshTokenSecurity()),
    user: User = Depends(UserRefreshTokenSecurity())
):
    token_manager = RefreshTokenManager(request, refresh)
    return await RefreshAuthRepository(
        request,
        response,
        token_manager,
        user
    ).run()

# TODO: DELETE 1 SEPTEMBER


@router.put("/", status_code=204)
async def add_refresh(
    request: Request,
    response: Response,
    refresh_token: str = Body(embed=True)
):
    domain = urlparse(request.headers.get("origin")).hostname
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/me/auth/session",
        max_age=7 * 24 * 3600,
        domain=domain
    )
