from datetime import timedelta
from fastapi import APIRouter, Request, Response
from app.models.user.user import User
from app.schemas.auth.auth import TokenResponse, UserCreate
from app.shared.utils.auth import AuthRepository
from app.shared.utils.registration import get_registration_handler

router = APIRouter()
EXPIRES_IN = int(timedelta(minutes=15).total_seconds())


class SignUp(AuthRepository[UserCreate]):
    async def get_user(self) -> User:
        handler = get_registration_handler(self.user_login)
        return await handler.register_user()


@router.post("/", response_model=TokenResponse)
async def register_user(user_create: UserCreate, request: Request, response: Response):
    return await SignUp(user_create, request, response).run()
