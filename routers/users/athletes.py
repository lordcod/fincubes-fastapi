from typing import List, Optional

from fastapi import APIRouter, Body, Depends, File, UploadFile

from misc.errors import APIError, ErrorCode
from misc.ratelimit import create_ratelimit
from misc.yandexcloud import delete_file, upload_file
from models.enums import UserRoleEnum
from models.models import Athlete, Coach, CoachAthlete
from routers.users.utils import get_role
from schemas.athlete import Athlete_Pydantic
from schemas.users.coach import CoachOut, CoachOutWithStatus

MAX_SIZE = 16 * 1024 * 1024
UPLOAD_INTERVAL_SECONDS = 60 * 60  # TODO REQUIRED CHANGE


async def get_content(file: UploadFile):
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise APIError(ErrorCode.FILE_TOO_LARGE)
    return content


router = APIRouter(prefix="/athletes")


@router.get("/", response_model=Athlete_Pydantic)
async def get_athlete_me(athlete: Athlete = Depends(get_role(UserRoleEnum.ATHLETE))):
    return await Athlete_Pydantic.from_tortoise_orm(athlete)


@router.put("/", response_model=Athlete_Pydantic)
async def edit_athlete_me(
    city: Optional[str] = Body(embed=True, default=None),
    club: Optional[str] = Body(embed=True, default=None),
    athlete: Athlete = Depends(get_role(UserRoleEnum.ATHLETE)),
):
    if city is None and club is None:
        raise APIError(ErrorCode.EMPTY_DATA)
    if club is not None and not club:
        raise APIError(ErrorCode.CLUB_CANNOT_BE_EMPTY)
    if club is not None:
        athlete.club = club
    if city is not None:
        athlete.city = city
    if city == "":
        athlete.city = None
    await athlete.save()
    return await Athlete_Pydantic.from_tortoise_orm(athlete)


@router.post("/avatar", response_model=Athlete_Pydantic)
async def upload_avatar(
    file: UploadFile = File(...),
    athlete: Athlete = Depends(get_role(UserRoleEnum.ATHLETE)),
    send_limit=Depends(create_ratelimit(
        "upload_avatar", UPLOAD_INTERVAL_SECONDS)),
):
    await send_limit(athlete.id)

    content = await get_content(file)
    ext = file.filename.split(".")[-1]

    avatar_url = await upload_file(content, f"{athlete.id}.{ext}")
    athlete.avatar_url = avatar_url
    await athlete.save()

    return await Athlete_Pydantic.from_tortoise_orm(athlete)


@router.delete("/avatar", response_model=Athlete_Pydantic)
async def delete_avatar(athlete: Athlete = Depends(get_role(UserRoleEnum.ATHLETE))):
    if athlete.avatar_url:
        await delete_file(url=athlete.avatar_url)
        athlete.avatar_url = None
        await athlete.save()
    return await Athlete_Pydantic.from_tortoise_orm(athlete)


@router.get("/coach/", response_model=List[CoachOutWithStatus])
async def get_coach(athlete: Athlete = Depends(get_role(UserRoleEnum.ATHLETE))):
    linked = await CoachAthlete.filter(athlete=athlete).select_related("coach")

    return [
        {**(await CoachOut.from_tortoise_orm(link.coach)).model_dump(), "status": link.status}
        for link in linked
    ]


@router.post("/coach/")
async def add_coach(
    coach_id: int = Body(embed=True),
    athlete: Athlete = Depends(get_role(UserRoleEnum.ATHLETE)),
):
    coach = await Coach.get(id=coach_id)
    link = await CoachAthlete.filter(coach=coach, athlete=athlete).first()

    if not link or link.status in ("pending", "rejected_athlete"):
        status = "accepted"
    else:
        return {"success": False, "status": link.status}
    if link:
        link.status = status
        await link.save()
    else:
        await CoachAthlete.create(coach=coach, athlete=athlete, status=status)
    return {"success": True, "status": status}


@router.delete("/coach/", status_code=204)
async def reject_coach(
    coach_id: int = Body(embed=True),
    athlete: Athlete = Depends(get_role(UserRoleEnum.ATHLETE)),
):
    coach = await Coach.get(id=coach_id)
    link = await CoachAthlete.filter(coach=coach, athlete=athlete).first()
    if not link:
        raise APIError(ErrorCode.ATHLETE_COACH_NOT_FOUND)

    link.status = "rejected_athlete"
    await link.save()
