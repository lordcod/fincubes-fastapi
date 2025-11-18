from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel
from app.integrations.yandexcloud import delete_file, upload_file
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


class UrlResponse(BaseModel):
    url: str


@router.post("/", response_model=UrlResponse)
@require_scope('file:create')
async def upload_file_cdn(
    filename: str,
    file: UploadFile = File(...)
):
    content = await file.read()
    url = await upload_file(content, filename)
    return {"url": url}


@router.delete("/", status_code=204)
@require_scope('file:delete')
async def delete_file_cdn(file_url: str):
    await delete_file(url=file_url)
