import logging

import jwt
from fastapi import Request
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.base import SecurityBase

from app.core.config import settings
from app.core.errors import APIError, ErrorCode
from app.models.user.user import User

from .schema import TokenType, UserAuthSecurityModel

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
_log = logging.getLogger(__name__)


class UserAuthSecurity(SecurityBase):
    def __init__(self, required_token_type: TokenType):
        super().__init__()

        self.required_token_type = required_token_type
        self.model = UserAuthSecurityModel()
        self.scheme_name = self.__class__.__name__

    async def __call__(self, request: Request) -> User:
        token = await oauth2_scheme(request)
        payload = self.validate_token(token)
        self.validate_token_type(payload)
        user = await self.get_user(payload)
        return user

    def validate_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(
                jwt=token,
                key=settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                leeway=1.0,
                options={"verify_sub": False},
            )
        except jwt.ExpiredSignatureError as exc:
            raise APIError(ErrorCode.EXPIRED_TOKEN) from exc
        except jwt.PyJWTError as exc:
            raise APIError(ErrorCode.INVALID_TOKEN) from exc
        return payload

    def validate_token_type(self, payload: dict):
        token_type = payload.get("type")
        if token_type != self.required_token_type:
            raise APIError(ErrorCode.INVALID_TYPE_TOKEN)

    async def get_user(self, payload: dict):
        id = payload.get("sub")
        if id is None:
            raise APIError(ErrorCode.INVALID_TOKEN)

        if isinstance(id, int):
            user = await User.get_or_none(id=id)
        else:
            user = await User.filter(email=id).first()
            _log.warning("User %s uses an outdated token system", id)

        if not user:
            raise APIError(ErrorCode.USER_NOT_FOUND)

        return user
