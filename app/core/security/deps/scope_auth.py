from fastapi import Request
from fastapi.params import Depends
from app.core.errors import APIError, ErrorCode
from app.core.security.deps.base_auth import BaseDecodeToken
from app.core.security.deps.base_interfaces import HTTPGetToken
from app.shared.clients.scopes.check import has_scope
from fastapi.security.base import SecurityBase
from app.core.security.schema import ApiKeySecurityModel


class ScopeAuthSecurity(Depends, SecurityBase, BaseDecodeToken, HTTPGetToken):
    def __init__(self, auto_error: bool = True):
        super().__init__(self)
        self.model = ApiKeySecurityModel()
        self.scheme_name = self.__class__.__name__
        self.auto_error = auto_error

    async def __call__(
        self,
        request: Request
    ) -> bool:
        scope = self.get_scope(request)
        if scope is None:
            return True
        try:
            token = await self.get_token(request)
            payload = self.decode_token(token)
            await self.resolve_entity(scope, payload)
        except APIError:
            if self.auto_error:
                raise
            return False
        else:
            return True

    def get_scope(self, request: Request):
        route = request.scope.get("endpoint")
        required_scope = getattr(route, "required_scope", None)
        return required_scope

    async def resolve_entity(self, scope: str, payload: dict) -> None:
        success = has_scope(payload.get('scopes', []), scope)
        if not success:
            raise APIError(ErrorCode.INSUFFICIENT_PRIVILEGES)
