from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi import HTTPException, Security, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2AuthorizationCodeBearer, OAuth2
from tortoise.exceptions import DoesNotExist
import jwt
from typing import Any
from misc.errors import APIError, ErrorCode
from models.models import User
from config import ALGORITHM, SECRET_KEY

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

PASSWORD_EXPIRATION_DAYS = 90


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(hashed_password: str, password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = timedelta(days=7)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise APIError(ErrorCode.INVALID_TOKEN)

        user = await User.filter(email=email).first()
        if not user:
            raise APIError(ErrorCode.USER_NOT_FOUND)

        return user
    except jwt.PyJWTError as exc:
        raise APIError(ErrorCode.INVALID_TOKEN) from exc


async def admin_required(current_user: User = Depends(get_current_user)) -> None:
    if not current_user.admin:
        raise APIError(ErrorCode.INSUFFICIENT_PRIVILEGES)
