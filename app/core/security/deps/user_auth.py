import logging
from app.models.user.user import User
from app.core.errors import APIError, ErrorCode
from app.core.security.deps.base_auth import BaseAuthSecurity
from app.core.security.schema import TokenType

_log = logging.getLogger(__name__)


class UserAuthSecurity(BaseAuthSecurity[User]):
    def __init__(self, required_token_type: TokenType):
        super().__init__(required_token_type, scope="user", scheme_type='bearer')

    async def resolve_entity(self, payload: dict) -> User:
        id = payload.get("sub")
        if id is None:
            raise APIError(ErrorCode.INVALID_TOKEN)

        if isinstance(id, int):
            user = await User.get_or_none(id=id)
        else:
            user = await User.filter(email=id).first()
            _log.warning("User %s uses an outdated token system", id)

        if not user:
            raise APIError(ErrorCode.USER_NOT_FOUND)
        return user
