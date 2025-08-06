from fastapi import Request
from app.core.security.deps.base_interfaces import BaseUserAuthSecurity
from app.core.errors import APIError, ErrorCode
from app.core.security.schema import TokenType, RefreshSecurityModel
from fastapi.security.base import SecurityBase


class RefreshTokenSecurity(SecurityBase, BaseUserAuthSecurity):
    def __init__(self):
        super().__init__(TokenType.refresh)
        self.model = RefreshSecurityModel()
        self.scheme_name = self.__class__.__name__

    async def get_token(self, request: Request) -> str:
        token = request.cookies.get("refresh_token")
        if not token:
            raise APIError(ErrorCode.INVALID_TOKEN)
        return token
