from enum import StrEnum

from fastapi.openapi.models import SecuritySchemeType
from fastapi.security.base import SecurityBase
from pydantic import Field


class TokenType(StrEnum):
    access = "access"
    refresh = "refresh"


class UserAuthSecurityModel(SecurityBase):
    type_: SecuritySchemeType = Field(
        default=SecuritySchemeType.apiKey, alias="type")
