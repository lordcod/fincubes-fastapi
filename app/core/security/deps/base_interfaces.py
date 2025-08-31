import logging
from typing import Generic, Tuple, TypeVar, Optional, Type

from fastapi import Request
from fastapi.security.base import SecurityBase

from app.core.errors import APIError, ErrorCode
from app.core.security.schema import TokenType, ApiKeySecurityModel
from app.core.security.deps.base_auth import BaseAuthSecurity, BaseGetToken, BaseResolveEntity, HTTPGetToken
from app.models.tokens.refresh_tokens import RefreshToken
from app.models.tokens.sessions import Session
from app.models.user.user import User


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


class CookieRefreshGetToken(BaseGetToken):
    async def get_token(self, request: Request) -> str:
        token = request.cookies.get("refresh_token")
        if not token:
            raise APIError(ErrorCode.INVALID_TOKEN)
        return token


class SessionResolveEntity(BaseResolveEntity[Session]):
    async def resolve_entity(self, payload: dict) -> Session:
        refresh = await RefreshToken.filter(access_id=payload['jti']).prefetch_related('session').first()
        return refresh.session


class UserResolveEntity(BaseResolveEntity[User]):
    async def resolve_entity(self, payload: dict) -> User:
        id = payload.get("sub")
        if id is None:
            raise APIError(ErrorCode.INVALID_TOKEN)

        user = await User.get_or_none(id=id)
        if not user:
            raise APIError(ErrorCode.USER_NOT_FOUND)
        return user


class PayloadResolveEntity(BaseResolveEntity[dict]):
    async def resolve_entity(self, payload: dict) -> dict:
        return payload
