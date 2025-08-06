import logging
from typing import Generic, Tuple, TypeVar, Optional, Type

from fastapi import Request
from fastapi.security.base import SecurityBase

from app.core.errors import APIError, ErrorCode
from app.core.security.schema import TokenType, ApiKeySecurityModel
from app.core.security.deps.base_auth import BaseAuthSecurity, HTTPGetToken
from app.models.user.user import User

_log = logging.getLogger(__name__)

T = TypeVar("T")  # Тип сущности: User, Bot и т.д.


class BaseHTTPAuthSecurity(SecurityBase, BaseAuthSecurity, HTTPGetToken):
    def __init__(self, required_token_type: TokenType, scheme_type: str | None = None):
        super().__init__(required_token_type)
        self.scheme_type = scheme_type
        self.model = ApiKeySecurityModel()
        self.scheme_name = self.__class__.__name__

    def check_token(self, schema: str, token: str):
        super().check_token(schema, token)
        if schema != self.scheme_type or not token:
            raise APIError(ErrorCode.INVALID_TOKEN)


class BaseUserAuthSecurity(BaseAuthSecurity[User]):
    async def resolve_entity(self, payload: dict) -> User:
        id = payload.get("sub")
        if id is None:
            raise APIError(ErrorCode.INVALID_TOKEN)

        user = await User.get_or_none(id=id)
        if not user:
            raise APIError(ErrorCode.USER_NOT_FOUND)
        return user
