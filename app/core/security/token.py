import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union

import jwt

from app.core.config import settings


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

    encoded_jwt = jwt.encode(data, settings.SECRET_KEY,
                             algorithm=settings.ALGORITHM)
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
