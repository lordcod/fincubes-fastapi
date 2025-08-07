from app.core.security.deps.base_interfaces import BaseHTTPAuthSecurity, BaseUserAuthSecurity
from app.core.security.schema import TokenType


class UserAuthSecurity(BaseUserAuthSecurity, BaseHTTPAuthSecurity):
    def __init__(self):
        super().__init__(TokenType.access, scheme_type='bearer')
