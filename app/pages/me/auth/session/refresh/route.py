from datetime import timedelta
from fastapi import APIRouter, Depends, Request
from jwtifypy import JWTManager

from app.core.security.deps.refresh_auth import RefreshTokenSecurity
from app.core.security.schema import TokenType
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
