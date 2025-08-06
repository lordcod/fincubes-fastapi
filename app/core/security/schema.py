from enum import StrEnum
from typing import Optional

from fastapi.openapi.models import SecuritySchemeType, SecurityBase, APIKeyIn
from pydantic import Field


class TokenType(StrEnum):
    access = "access"
    refresh = "refresh"
    service = "service"
    protection = "protection"


class ApiKeySecurityModel(SecurityBase):
    type_: SecuritySchemeType = Field(
        default=SecuritySchemeType.apiKey,
        alias="type",
        description="Тип схемы безопасности. Здесь используется apiKey."
    )
    in_: APIKeyIn = Field(default=APIKeyIn.header, alias="in")
    name: str = Field(default="Authorization")
    description: Optional[str] = Field(
        default="Авторизация по токену доступа пользователя.",
        description="Описание схемы безопасности, выводится в OpenAPI."
    )


class RefreshSecurityModel(SecurityBase):
    type_: SecuritySchemeType = Field(
        default=SecuritySchemeType.apiKey,
        alias="type",
        description="Тип схемы безопасности. Здесь используется apiKey."
    )
    in_: APIKeyIn = Field(default=APIKeyIn.cookie, alias="in")
    name: str = Field(default="refresh_token")
    description: Optional[str] = Field(
        default="Аутентификация с использованием refresh-токена, передаваемого через cookie.",
        description="Описание схемы безопасности, выводится в OpenAPI."
    )


# class UserAuthSecurityModel(SecurityBase):
#     type_: SecuritySchemeType = Field(
#         default=SecuritySchemeType.http,
#         alias="type",
#         description="Тип схемы безопасности: HTTP Bearer Authentication."
#     )
#     scheme: str = Field(
#         default="bearer",
#         description="Схема авторизации HTTP (обычно bearer)."
#     )
#     bearerFormat: Optional[str] = Field(
#         default="JWT",
#         description="Формат токена, например JWT."
#     )
#     description: Optional[str] = Field(
#         default="Авторизация по токену доступа пользователя.",
#         description="Описание схемы безопасности, отображаемое в документации."
#     )
