from fastapi import APIRouter, Depends

from app.core.errors import APIError, ErrorCode
from app.core.security.auth import UserAuthSecurity
from app.core.security.hashing import hash_password, verify_password
from app.core.security.schema import TokenType
from app.models.user.user import User

router = APIRouter()


@router.put("/", status_code=204)
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(UserAuthSecurity(TokenType.access)),
):
    if not verify_password(current_user.hashed_password, current_password):
        raise APIError(ErrorCode.INCORRECT_CURRENT_PASSWORD)

    hashed_new_password = hash_password(new_password)
    current_user.hashed_password = hashed_new_password
    await current_user.save()
