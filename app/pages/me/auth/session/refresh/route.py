from fastapi import APIRouter, Depends, Request

from app.core.security.deps.user_auth import UserAuthSecurity
from app.core.security.schema import TokenType
from app.core.security.token import create_access_token
from app.models.user.user import User
from app.schemas.auth.auth import TokenResponse

router = APIRouter()


@router.post("/", response_model=TokenResponse)
async def refresh(
    request: Request,
    current_user: User = Depends(UserAuthSecurity(TokenType.refresh)),
):
    access_token = create_access_token(
        current_user.id,
        fresh=False,
        issuer=request.url.path,
        audience="auth",
    )

    return {"refresh_token": None, "access_token": access_token, "token_type": "Bearer"}
