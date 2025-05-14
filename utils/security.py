from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi import HTTPException, Security, Depends
from fastapi.security import OAuth2PasswordBearer
from tortoise.exceptions import DoesNotExist
import jwt
from typing import Any
from models.models import User
from config import ALGORITHM, SECRET_KEY

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

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
            raise HTTPException(status_code=403, detail="Invalid token")

        user = await User.filter(email=email).first()
        if not user:
            raise HTTPException(status_code=403, detail="User not found")

        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Invalid token")


async def admin_required(current_user: User = Depends(get_current_user)) -> None:
    if not current_user.admin:
        raise HTTPException(status_code=403, detail="Insufficient privileges")
