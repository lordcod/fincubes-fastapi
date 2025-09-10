import asyncio
import hashlib
from fastapi import APIRouter, Depends, File, UploadFile

from app.core.deps.ratelimit import create_ratelimit
from app.core.errors import APIError, ErrorCode
from app.integrations.yandex_cdn_api import update_cdn_cache
from app.integrations.yandexcloud import delete_file, extract_object_path, upload_file
from app.models.athlete.athlete import Athlete
from app.schemas.athlete.athlete import Athlete_Pydantic
from app.shared.enums.enums import UserRoleEnum
from app.shared.utils.user_role import get_role

router = APIRouter()

MAX_SIZE = 16 * 1024 * 1024
UPLOAD_INTERVAL_SECONDS = 60 * 60


async def get_content(file: UploadFile):
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise APIError(ErrorCode.FILE_TOO_LARGE)
    return content


router = APIRouter()


@router.post("/", response_model=Athlete_Pydantic)
async def upload_avatar(
    file: UploadFile = File(...),
    athlete: Athlete = Depends(get_role(UserRoleEnum.ATHLETE)),
    send_limit=Depends(create_ratelimit(
        "upload_avatar", UPLOAD_INTERVAL_SECONDS)),
):
    await send_limit(athlete.id)

    content = await get_content(file)
    ext = file.filename.split(".")[-1]
    hash = hashlib.sha256(content).hexdigest()

    filename = f"avatar/{athlete.id}_{hash[:16]}.{ext}"
    avatar_url, _ = await asyncio.gather(
        upload_file(content, filename),
        update_cdn_cache(filename, action='prefetch')
    )
    athlete.avatar_url = avatar_url
    await athlete.save()

    return await Athlete_Pydantic.from_tortoise_orm(athlete)


@router.delete("/", response_model=Athlete_Pydantic)
async def delete_avatar(athlete: Athlete = Depends(get_role(UserRoleEnum.ATHLETE))):
    if athlete.avatar_url:
        await delete_file(url=athlete.avatar_url)
        athlete.avatar_url = None
        await athlete.save()
    return await Athlete_Pydantic.from_tortoise_orm(athlete)
