from app.core.security.deps.base_interfaces import BaseHTTPAuthSecurity, UserResolveEntity
from app.core.security.schema import TokenType


class UserAuthSecurity(UserResolveEntity, BaseHTTPAuthSecurity):
    def __init__(self):
        super().__init__(TokenType.access, scheme_type='bearer')
