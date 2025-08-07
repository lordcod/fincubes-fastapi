from datetime import timedelta
from urllib.parse import urlparse
from fastapi import APIRouter, Body, Depends, Request, Response
from jwtifypy import JWTManager

from app.core.security.deps.refresh_auth import RefreshTokenSecurity
from app.models.user.user import User
from app.schemas.auth.auth import TokenResponse

router = APIRouter()
EXPIRES_IN = int(timedelta(minutes=15).total_seconds())


@router.post("/", response_model=TokenResponse)
async def refresh(
    request: Request,
    current_user: User = Depends(RefreshTokenSecurity()),
):
    manager = JWTManager.with_issuer(request.url.path).with_audience("auth")
    access_token = manager.create_access_token(current_user.id, fresh=False)

    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": EXPIRES_IN
    }

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
