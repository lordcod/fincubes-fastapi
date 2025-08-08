import logging
from typing import Optional, Protocol, Tuple, TypeVar, Generic
from abc import ABC, abstractmethod

from fastapi import Request
from fastapi.params import Depends
import jwt
from pydantic import conset
from app.core.errors import APIError, ErrorCode
from jwtifypy import JWTManager

from ..schema import TokenType
T = TypeVar("T")


class BaseGetToken(ABC):
    @abstractmethod
    async def get_token(self, request: Request) -> str:
        ...


class BaseCheckPayload(ABC):
    @abstractmethod
    def check_payload(self, payload: dict) -> None: ...


class BaseResolveEntity(ABC, Generic[T]):
    @abstractmethod
    async def resolve_entity(self, payload: dict) -> T: ...


class BaseDecodeToken:
    def decode_token(self, token: str) -> dict:
        try:
            payload = JWTManager.decode_token(token)
        except jwt.ExpiredSignatureError as exc:
            raise APIError(ErrorCode.EXPIRED_TOKEN) from exc
        except jwt.PyJWTError as exc:
            raise APIError(ErrorCode.INVALID_TOKEN) from exc
        return payload


class CheckTokenType(BaseCheckPayload):
    def __init__(
        self,
        required_token_type: TokenType,
    ):
        self.required_token_type = required_token_type

    def check_payload(self, payload: dict):
        token_type = payload.get("type")
        if token_type != self.required_token_type:
            raise APIError(ErrorCode.INVALID_TYPE_TOKEN)


class HTTPGetToken(BaseGetToken):
    async def get_token(self, request: Request) -> str:
        schema, token = self.extract_token(request)
        self.check_token(schema, token)
        return token

    def extract_token(self, request: Request) -> Tuple[str, str]:
        authorization = request.headers.get("Authorization")
        return self.parse_authorization_header(authorization)

    def check_token(self, schema: str, token: str):
        if not token:
            raise APIError(ErrorCode.INVALID_TOKEN)

    def parse_authorization_header(
        self,
        authorization_header_value: Optional[str],
    ) -> Tuple[str, str]:
        if not authorization_header_value:
            return "", ""
        scheme, _, param = authorization_header_value.partition(" ")
        return scheme.lower(), param


class BaseAuthSecurity(Generic[T],
                       Depends,
                       BaseDecodeToken,
                       BaseGetToken,
                       CheckTokenType,
                       BaseResolveEntity[T]):
    def __init__(
        self,
        required_token_type: TokenType,
    ):
        Depends.__init__(self, self)
        CheckTokenType.__init__(self, required_token_type)

    async def __call__(self, request: Request) -> T:
        token = await self.get_token(request)
        payload = self.decode_token(token)
        self.check_payload(payload)
        return await self.resolve_entity(payload)
