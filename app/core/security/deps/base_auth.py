import logging
from typing import Optional, Tuple, TypeVar, Generic
from abc import ABC, abstractmethod

from fastapi import Request
from fastapi.params import Depends, Security
import jwt
from app.core.errors import APIError, ErrorCode
from jwtifypy import JWTManager

from ..schema import TokenType

_log = logging.getLogger(__name__)
T = TypeVar("T")


class BaseAuthSecurity(Security, Generic[T], ABC):
    def __init__(
        self,
        required_token_type: TokenType,
        scheme_type: Optional[str] = None,
    ):
        super().__init__(self, scopes=['app'])
        self.required_token_type = required_token_type
        self.scheme_type = scheme_type

    async def __call__(self, request: Request) -> T:
        token = await self.get_token(request)
        payload = self.decode_token(token)
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

    def decode_token(self, token: str) -> dict:
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
    async def get_token(self, request: Request) -> str:
        ...

    @abstractmethod
    async def resolve_entity(self, payload: dict) -> T:
        ...
