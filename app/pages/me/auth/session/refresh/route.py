from fastapi import APIRouter, Depends, Request
from jwtifypy import JWTManager

from app.core.security.deps.user_auth import UserAuthSecurity
from app.core.security.schema import TokenType
from app.models.user.user import User
from app.schemas.auth.auth import TokenResponse

router = APIRouter()


@router.post("/", response_model=TokenResponse)
async def refresh(
    request: Request,
    current_user: User = Depends(UserAuthSecurity(TokenType.refresh)),
):
    manager = JWTManager.with_issuer(request.url.path).with_audience("auth")
    access_token = manager.create_access_token(current_user.id, fresh=False)

    return {"refresh_token": None, "access_token": access_token, "token_type": "Bearer"}
