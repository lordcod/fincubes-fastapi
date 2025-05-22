from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Body,  Depends, File, HTTPException, UploadFile
from fastapi.background import P
from misc.errors import APIError, ErrorCode
from models.deps import get_redis
from models.enums import UserRoleEnum
from models.models import Athlete, Coach, CoachAthlete
from routers.users.utils import get_role
from schemas.athlete import Athlete_Pydantic
from misc.yandexcloud import delete_file, upload_file
from redis.asyncio import Redis as RedisClient

from schemas.users.coach import CoachOut

MAX_SIZE = 16 * 1024 * 1024
UPLOAD_INTERVAL_SECONDS = 60 * 60


async def get_content(file: UploadFile):
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="Файл слишком большой")
    return content


router = APIRouter(
    prefix='/athletes')


@router.get('/', response_model=Athlete_Pydantic)
async def get_athlete_me(athlete: Athlete = Depends(get_role(UserRoleEnum.ATHLETE))):
    return await Athlete_Pydantic.from_tortoise_orm(athlete)


@router.put('/', response_model=Athlete_Pydantic)
async def edit_athlete_me(
    city: Optional[str] = Body(embed=True, default=None),
    club: Optional[str] = Body(embed=True, default=None),
    athlete: Athlete = Depends(get_role(UserRoleEnum.ATHLETE))
):
    if city is None and club is None:
        raise HTTPException(detail="Пустые данные", status_code=422)
    if club is not None and not club:
        raise HTTPException(
            detail="Клуб не может быть пустым", status_code=422)
    if club is not None:
        athlete.club = club
    if city is not None:
        athlete.city = city
    if city == "":
        athlete.city = None
    await athlete.save()
    return await Athlete_Pydantic.from_tortoise_orm(athlete)


@router.post('/avatar', response_model=Athlete_Pydantic)
async def upload_avatar(
    file: UploadFile = File(...),
    athlete: Athlete = Depends(get_role(UserRoleEnum.ATHLETE)),
    redis: RedisClient = Depends(get_redis)
):
    key = f"last_avatar_upload:{athlete.id}"
    now = datetime.now().timestamp()
    last_upload_timestamp = await redis.get(key)
    if last_upload_timestamp:
        last = float(last_upload_timestamp)
        if now - last < UPLOAD_INTERVAL_SECONDS:
            raise HTTPException(
                status_code=429, detail="Аватарку можно изменять раз в час.")
    await redis.set(key, now)

    content = await get_content(file)
    ext = file.filename.split('.')[-1]
    if athlete.avatar_url:
        await delete_file(url=athlete.avatar_url)

    avatar_url = await upload_file(content, f'{athlete.id}.{ext}')
    athlete.avatar_url = avatar_url
    await athlete.save()

    return await Athlete_Pydantic.from_tortoise_orm(athlete)


@router.delete('/avatar', response_model=Athlete_Pydantic)
async def delete_avatar(
    athlete: Athlete = Depends(get_role(UserRoleEnum.ATHLETE))
):
    athlete.avatar_url = None
    await athlete.save()
    return await Athlete_Pydantic.from_tortoise_orm(athlete)


@router.get('/coach/', response_model=List[CoachOut])
async def get_coach(
    athlete: Athlete = Depends(get_role(UserRoleEnum.ATHLETE))
):
    linked = await CoachAthlete.filter(
        athlete=athlete).select_related('coach')
    return [await CoachOut.from_tortoise_orm(link.athlete)
            for link in linked]


@router.post('/coach/')
async def add_coach(
    coach_id: int = Body(embed=True),
    athlete: Athlete = Depends(get_role(UserRoleEnum.ATHLETE))
):
    coach = await Coach.get(id=coach_id)
    link = await CoachAthlete.filter(coach=coach, athlete=athlete).first()

    if not link or link.status in ('pending', 'rejected_athlete'):
        status = 'accepted'
    else:
        return {
            'success': False,
            'status': link.status
        }

    await CoachAthlete.create(coach=coach, athlete=athlete, status=status)
    return {
        'success': True,
        'status': status
    }


@router.delete('/coach/', status_code=204)
async def reject_coach(
    athlete_id: int = Body(embed=True),
    coach: Coach = Depends(get_role(UserRoleEnum.COACH))
):
    athlete = await Athlete.get(id=athlete_id)
    link = await CoachAthlete.filter(coach=coach, athlete=athlete).first()
    if not link:
        raise APIError(ErrorCode.ATHLETE_COACH_NOT_FOUND)

    link.status = 'rejected_athlete'
    await link.save()
