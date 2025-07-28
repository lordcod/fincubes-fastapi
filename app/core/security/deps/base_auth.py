import logging
from typing import Optional, Tuple, TypeVar, Generic
from abc import ABC, abstractmethod

from fastapi import Request
from fastapi.params import Security
from fastapi.security.base import SecurityBase
import jwt

from app.core.config import settings
from app.core.errors import APIError, ErrorCode
from jwtifypy import JWTManager

from ..schema import TokenType, AuthSecurityModel

_log = logging.getLogger(__name__)
T = TypeVar("T")


class BaseAuthSecurity(SecurityBase, Security, Generic[T], ABC):
    def __init__(
        self,
        required_token_type: TokenType,
        scope: str,
        scheme_type: str
    ):
        super().__init__(self, scopes=[scope])
        self.required_token_type = required_token_type
        self.scheme_type = scheme_type
        self.model = AuthSecurityModel()
        self.scheme_name = self.__class__.__name__

    async def __call__(self, request: Request) -> T:
        authorization = request.headers.get("Authorization")
        scheme, token = self.parse_authorization_header(authorization)
        payload = self.decode_token(scheme, token)
        self.check_token(payload)
        return await self.resolve_entity(payload)

    def parse_authorization_header(
        self,
        authorization_header_value: Optional[str],
    ) -> Tuple[str, str]:
        if not authorization_header_value:
            return "", ""
        scheme, _, param = authorization_header_value.partition(" ")
        return scheme.lower(), param

    def decode_token(self, scheme: str, token: str) -> dict:
        if scheme != self.scheme_type:
            raise APIError(ErrorCode.INVALID_TOKEN)
        try:
            payload = JWTManager.decode_token(token)
        except jwt.ExpiredSignatureError as exc:
            raise APIError(ErrorCode.EXPIRED_TOKEN) from exc
        except jwt.PyJWTError as exc:
            raise APIError(ErrorCode.INVALID_TOKEN) from exc
        return payload

    def check_token(self, payload: dict):
        token_type = payload.get("type")
        if token_type != self.required_token_type:
            raise APIError(ErrorCode.INVALID_TYPE_TOKEN)

    @abstractmethod
    async def resolve_entity(self, payload: dict) -> T:
        ...
