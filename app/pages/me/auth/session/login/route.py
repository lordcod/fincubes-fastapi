from datetime import timedelta
from fastapi import APIRouter, Request, Response

from app.core.errors import APIError, ErrorCode
from app.core.security.hashing import verify_password
from app.models.user.user import User
from app.schemas.auth.auth import TokenResponse, UserLogin
from app.shared.utils.auth import AuthRepository

router = APIRouter()
EXPIRES_IN = int(timedelta(minutes=15).total_seconds())


class Login(AuthRepository[UserLogin]):
    async def get_user(self) -> User:
        user = await User.filter(email=self.user_login.email).first()
        if not user:
            raise APIError(ErrorCode.USER_NOT_FOUND)

        if not verify_password(self.user_login.password, user.hashed_password):
            raise APIError(ErrorCode.INCORRECT_CURRENT_PASSWORD)

        return user


@router.post("/", response_model=TokenResponse)
async def login_user(user_login: UserLogin, request: Request, response: Response):
    return await Login(user_login, request, response).run()
