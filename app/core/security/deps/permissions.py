from fastapi import Depends

from app.core.errors import APIError, ErrorCode
from app.models.user.user import User

from .user_auth import UserAuthSecurity


async def admin_required(current_user: User = Depends(UserAuthSecurity())) -> None:
    if not current_user.admin:
        raise APIError(ErrorCode.INSUFFICIENT_PRIVILEGES)
