from fastapi import Request
from fastapi.params import Depends, Security
from app.core.errors import APIError, ErrorCode
from app.core.security.deps.base_auth import BaseAuthSecurity
from app.core.security.schema import ApiKeySecurityModel, TokenType
from app.models.misc.bot import Bot
from fastapi.security.base import SecurityBase


class BotAuthSecurity(SecurityBase, BaseAuthSecurity[Bot]):
    def __init__(self):
        BaseAuthSecurity.__init__(
            self,
            required_token_type=TokenType.service,
            scheme_type='bot'
        )
        self.model = ApiKeySecurityModel()
        self.scheme_name = self.__class__.__name__

    async def get_token(self, request: Request) -> str:
        authorization = request.headers.get("Authorization")
        scheme, token = self.parse_authorization_header(authorization)
        if scheme != self.scheme_type or not token:
            raise APIError(ErrorCode.INVALID_TOKEN)
        return token

    async def resolve_entity(self, payload: dict) -> Bot:
        id = payload.get("sub")
        if id is None:
            raise APIError(ErrorCode.INVALID_TOKEN)

        if isinstance(id, int):
            bot = await Bot.get_or_none(id=id)
        else:
            bot = None

        if not bot:
            raise APIError(ErrorCode.BOT_NOT_FOUND)
        if not bot.is_active:
            raise APIError(ErrorCode.BOT_DISABLED)

        return bot
