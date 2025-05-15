from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from tortoise import Tortoise
from tortoise.exceptions import DoesNotExist
from models.models import Athlete, User
from schemas.auth import UserCreate, UserLogin, UserResponse, TokenResponse, UserResponseAthlete
from passlib.context import CryptContext
from datetime import datetime
import jwt
from jwt import PyJWTError
from utils.security import admin_required, get_current_user, hash_password, verify_password, create_access_token
from utils.cloudflare import check_verification


router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"

# Проверка токена (middleware)


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Токен истек")
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Не авторизован")


@router.get("/users/me", response_model=UserResponse)
async def protected_endpoint(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/users/athlete/{athlete_id}", dependencies=[Depends(admin_required)], response_model=Optional[UserResponseAthlete])
async def get_user_from_athlete_id(athlete_id: int):
    try:
        user = await User.filter(athlete_id=athlete_id).prefetch_related("athlete").first()
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/users/{user_id}/unassign-athlete", dependencies=[Depends(admin_required)])
async def unassign_athlete(user_id: int):
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.athlete = None
    await user.save()
    return {"detail": "Athlete unassigned"}


@router.post("/users/{user_id}/assign-athlete/{athlete_id}", dependencies=[Depends(admin_required)])
async def assign_athlete(user_id: int, athlete_id: int):
    try:
        user = await User.get(id=user_id)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        athlete = await Athlete.get(id=athlete_id)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Athlete not found")

    if user.athlete:
        raise HTTPException(
            status_code=400, detail="User already has an athlete")

    user.athlete = athlete
    await user.save()


@router.post("/users/{user_id}/set-admin", dependencies=[Depends(admin_required)])
async def set_admin_status(user_id: int, value: bool):
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.admin = value
    await user.save()
    return {"detail": f"Admin status set to {value}"}


@router.get("/users/search", dependencies=[Depends(admin_required)], response_model=List[UserResponseAthlete])
async def search_users(q: str):
    if q.isdigit():
        users = User.filter(id=int(q)).all()
    else:
        users = User.filter(email__icontains=q).all()
    users = await users.prefetch_related("athlete")
    return users


@router.post("/register", response_model=TokenResponse)
async def register_user(user_create: UserCreate):
    ts = await check_verification(user_create.cf_token)
    if not ts.success:
        codes = ', '.join(ts.error_codes)
        raise HTTPException(
            status_code=400, detail=f"Ошибка капчи {codes}")

    user = await User.filter(email=user_create.email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email уже занят")
    if user_create.athlete_id:
        try:
            athlete = await Athlete.get(id=user_create.athlete_id)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Атлет не найден")

        if await User.filter(athlete_id=athlete.id).exists():
            raise HTTPException(status_code=400, detail="Атлет уже занят")

    hashed_password = hash_password(user_create.password)

    user = await User.create(
        email=user_create.email,
        hashed_password=hashed_password,
        athlete_id=user_create.athlete_id
    )

    access_token = create_access_token(data={"sub": user.email})

    return {"access_token": access_token, "token_type": "Bearer"}


@router.post("/login", response_model=TokenResponse)
async def login_user(user_login: UserLogin):
    ts = await check_verification(user_login.cf_token)
    if not ts.success:
        codes = ', '.join(ts.error_codes)
        raise HTTPException(
            status_code=400, detail=f"Ошибка капчи {codes}")

    user = await User.filter(email=user_login.email).first()
    if not user:
        raise HTTPException(
            status_code=400, detail="Неверный email или пароль")

    if not pwd_context.verify(user_login.password, user.hashed_password):
        raise HTTPException(
            status_code=400, detail="Неверный email или пароль")

    access_token = create_access_token(data={"sub": user.email})

    return {"access_token": access_token, "token_type": "  Bearer"}


@router.put("/change-password", status_code=204)
async def change_password(current_password: str, new_password: str, current_user: User = Depends(get_current_user)):
    if not verify_password(current_user.hashed_password, current_password):
        raise HTTPException(
            status_code=400, detail="Incorrect current password")

    hashed_new_password = hash_password(new_password)
    current_user.hashed_password = hashed_new_password
    await current_user.save()
