from app.core.errors import APIError, ErrorCode
from app.core.security.deps.base_auth import BaseAuthSecurity
from app.core.security.deps.base_interfaces import BaseHTTPAuthSecurity
from app.core.security.schema import TokenType
from app.models.misc.bot import Bot


class BotAuthSecurity(BaseHTTPAuthSecurity, BaseAuthSecurity[Bot]):
    def __init__(self):
        super().__init__(
            required_token_type=TokenType.service,
            scheme_type='bot'
        )

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
