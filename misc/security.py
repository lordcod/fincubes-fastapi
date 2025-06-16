import logging
import traceback
import uuid
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Any, Optional, Union

import jwt
from fastapi import Depends, Request
from fastapi.openapi.models import SecuritySchemeType
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.base import SecurityBase
from passlib.context import CryptContext
from pydantic import Field

from config import ALGORITHM, SECRET_KEY
from misc.errors import APIError, ErrorCode
from models.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
_log = logging.getLogger(__name__)

PASSWORD_EXPIRATION_DAYS = 90


class TokenType(StrEnum):
    access: str = "access"
    refresh: str = "refresh"


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(hashed_password: str, password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def _create_token(
    subject: Union[str, int],
    type_token: str,
    fresh: Optional[bool] = False,
    issuer: Optional[str] = None,
    audience: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,  # timedelta(days=7)
    **user_claims: Any
) -> str:
    now = datetime.now(tz=timezone.utc)
    jwt_id = str(uuid.uuid4())
    issued_at = now
    not_before = now
    data = {
        "type": type_token,
        "sub": subject,
        "jti": jwt_id,
        "nbf": not_before,
        "iat": issued_at,
    }
    if type_token == "access":
        data["fresh"] = fresh
    if issuer is not None:
        data["iss"] = issuer
    if audience is not None:
        data["aud"] = audience
    if expires_delta is not None:
        data["exp"] = now + expires_delta
    if user_claims:
        data.update(user_claims)

    encoded_jwt = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_access_token(
    subject: Union[str, int],
    fresh: Optional[bool] = False,
    expires_delta: Optional[timedelta] = timedelta(minutes=15),
    issuer: Optional[str] = None,
    audience: Optional[str] = None,
) -> str:
    return _create_token(
        subject=subject,
        type_token="access",
        fresh=fresh,
        expires_delta=expires_delta,
        issuer=issuer,
        audience=audience,
    )


def create_refresh_token(
    subject: Union[str, int],
    expires_delta: Optional[timedelta] = timedelta(days=31),
    issuer: Optional[str] = None,
    audience: Optional[str] = None,
) -> str:
    return _create_token(
        subject=subject,
        type_token="refresh",
        expires_delta=expires_delta,
        issuer=issuer,
        audience=audience,
    )


class UserAuthSecurityModel(SecurityBase):
    type_: SecuritySchemeType = Field(default=SecuritySchemeType.apiKey, alias="type")


class UserAuthSecurity(SecurityBase):
    def __init__(self, required_token_type: TokenType):
        super().__init__()

        self.required_token_type = required_token_type
        self.model = UserAuthSecurityModel()
        self.scheme_name = self.__class__.__name__

    async def __call__(self, request: Request) -> User:
        token = await oauth2_scheme(request)
        payload = self.validate_token(token)
        self.validate_token_type(payload)
        user = await self.get_user(payload)
        return user

    def validate_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(
                jwt=token,
                key=SECRET_KEY,
                algorithms=[ALGORITHM],
                leeway=1.0,
                options={"verify_sub": False},
            )
        except jwt.ExpiredSignatureError as exc:
            raise APIError(ErrorCode.EXPIRED_TOKEN) from exc
        except jwt.PyJWTError as exc:
            traceback.print_exception(exc)
            raise APIError(ErrorCode.INVALID_TOKEN) from exc
        return payload

    def validate_token_type(self, payload: dict):
        token_type = payload.get("type")
        # TODO DELETE 21 JUNE
        if token_type and token_type != self.required_token_type:
            raise APIError(ErrorCode.INVALID_TYPE_TOKEN)

    async def get_user(self, payload: dict):
        id = payload.get("sub")
        if id is None:
            raise APIError(ErrorCode.INVALID_TOKEN)

        if isinstance(id, int):
            user = await User.get_or_none(id=id)
        else:
            # TODO DELETE 21 JUNE
            user = await User.filter(email=id).first()
            _log.warning("User %s uses an outdated token system", id)

        if not user:
            raise APIError(ErrorCode.USER_NOT_FOUND)

        return user


async def admin_required(
    current_user: User = Depends(UserAuthSecurity(TokenType.access)),
) -> None:
    if not current_user.admin:
        raise APIError(ErrorCode.INSUFFICIENT_PRIVILEGES)
