from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, EmailStr, Field
from tortoise.contrib.pydantic import pydantic_model_creator

from app.models.user.user import User

UserResponse = pydantic_model_creator(User, exclude=("hashed_password",))


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    cf_token: str

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    cf_token: str
    role: Optional[Literal["athlete", "coach", "parent"]] = None
    metadata: Dict[str, Any]

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(
        default="bearer", description="Тип токена (обычно 'bearer')")
    expires_in: int = Field(...,
                            description="Время жизни access токена в секундах")

    class Config:
        from_attributes = True
