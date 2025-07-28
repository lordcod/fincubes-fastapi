import logging

from fastapi import Request
from fastapi.params import Depends
from app.models.user.user import User
from app.core.errors import APIError, ErrorCode
from app.core.security.deps.base_auth import BaseAuthSecurity
from app.core.security.schema import TokenType, ApiKeySecurityModel, RefreshSecurityModel
from fastapi.security.base import SecurityBase

_log = logging.getLogger(__name__)


class RefreshTokenSecurity(SecurityBase, BaseAuthSecurity[User]):
    def __init__(self):
        super().__init__(TokenType.refresh, scheme_type='bearer')
        self.model = RefreshSecurityModel()
        self.scheme_name = self.__class__.__name__

    async def get_token(self, request: Request) -> str:
        token = request.cookies.get("refresh_token")
        if not token:
            raise APIError(ErrorCode.INVALID_TOKEN)
        return token

    async def resolve_entity(self, payload: dict) -> User:
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


class UserAuthSecurity(SecurityBase, BaseAuthSecurity[User]):
    def __init__(self):
        BaseAuthSecurity.__init__(self, TokenType.access, scheme_type='bearer')
        self.model = ApiKeySecurityModel()
        self.scheme_name = self.__class__.__name__

    async def get_token(self, request: Request) -> str:
        authorization = request.headers.get("Authorization")
        scheme, token = self.parse_authorization_header(authorization)
        if scheme != self.scheme_type or not token:
            raise APIError(ErrorCode.INVALID_TOKEN)
        return token

    async def resolve_entity(self, payload: dict) -> User:
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
