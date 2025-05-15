import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

from schemas import Athlete_Pydantic


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
    athlete_id: Optional[int] = None

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime.datetime
    admin: bool
    premium: bool
    athlete_id: Optional[int] = None

    class Config:
        from_attributes = True


class UserResponseAthlete(UserResponse):
    athlete: Optional[Athlete_Pydantic] = None

    class Config:
        from_attributes = True

# Модель для ответа на создание пользователя


# Модель для ответа на создание пользователя


class TokenResponse(BaseModel):
    access_token: str
    token_type: str

    class Config:
        from_attributes = True
