from app.core.security.deps.base_interfaces import BaseHTTPAuthSecurity, SessionResolveEntity, UserResolveEntity
from app.core.security.schema import TokenType


class UserAuthSecurity(UserResolveEntity, BaseHTTPAuthSecurity):
    def __init__(self):
        super().__init__(TokenType.access, scheme_type='bearer')


class SessionAuthSecurity(SessionResolveEntity, BaseHTTPAuthSecurity):
    def __init__(self):
        super().__init__(TokenType.access, scheme_type='bearer')
