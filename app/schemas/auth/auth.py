from typing import Any, Dict, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from tortoise.contrib.pydantic import pydantic_model_creator

from app.models.user.user import User
from app.schemas import with_nested
from app.schemas.athlete.athlete import Athlete_Pydantic

UserResponse = pydantic_model_creator(User, exclude=("hashed_password",))


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    cf_token: str

    model_config = ConfigDict(from_attributes=True)


class UserCreate(UserLogin):
    role: Optional[Literal["athlete", "coach", "parent"]] = None
    metadata: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(
        default="bearer", description="Тип токена (обычно 'bearer')")
    expires_in: int = Field(...,
                            description="Время жизни access токена в секундах")

    model_config = ConfigDict(from_attributes=True)
