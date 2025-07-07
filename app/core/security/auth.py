import logging
from typing import Optional, Tuple

import jwt
from fastapi import Request
from fastapi.params import Security
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.base import SecurityBase

from app.core.config import settings
from app.core.errors import APIError, ErrorCode
from app.models.user.user import User

from .schema import TokenType, UserAuthSecurityModel
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
_log = logging.getLogger(__name__)


class UserAuthSecurity(SecurityBase, Security):
    def __init__(self, required_token_type: TokenType):
        super().__init__(self, scopes=["user"])

        self.required_token_type = required_token_type
        self.model = UserAuthSecurityModel()
        self.scheme_name = self.__class__.__name__

    async def __call__(self, request: Request) -> User:
        authorization = request.headers.get('Authorization')
        scheme, param = self.get_authorization_scheme_param(authorization)
        payload = self.validate_token(scheme, param)
        self.validate_token_type(payload)
        user = await self.get_user(payload)
        return user

    def get_authorization_scheme_param(
        self,
        authorization_header_value: Optional[str],
    ) -> Tuple[str, str]:
        if not authorization_header_value:
            return "", ""
        scheme, _, param = authorization_header_value.partition(" ")
        return scheme.lower(), param

    def validate_token(self, scheme: str, token: str) -> dict:
        if scheme != 'bearer':
            raise APIError(ErrorCode.INVALID_TOKEN)
        try:
            payload = jwt.decode(
                jwt=token,
                key=settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                leeway=1.0,
                options={"verify_sub": False,
                         "verify_aud": False,
                         "verify_iss": False},
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
