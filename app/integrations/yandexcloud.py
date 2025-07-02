import hashlib
from typing import Optional

from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials

from app.core.config import settings
from app.shared.clients import session

credentials = Credentials(settings.AWS_KEY_ID, settings.AWS_SECRET_KEY)
CLOUD_API_URL = 'https://storage.yandexcloud.net'
CDN_URL = 'https://cdn.fincubes.ru'


async def upload_file(body: bytes, object_path: str):
    url = f"{CLOUD_API_URL}/{settings.BUCKET_NAME}/{object_path}"

    body_hash = hashlib.sha256(body).hexdigest()

    request = AWSRequest(method="PUT", url=url, data=body)
    request.headers["x-amz-content-sha256"] = body_hash
    SigV4Auth(credentials, "s3", "ru-central1").add_auth(request)

    async with session.session.put(
        url, data=body, headers=dict(request.headers)
    ) as response:
        if response.status >= 400:
            text = await response.text()
            raise Exception(f"Upload failed: {response.status} {text}")
        return f'{CDN_URL}/{object_path}'


async def delete_file(*, url: Optional[str] = None, object_path: Optional[str] = None):
    if url is None and object_path is None:
        raise ValueError("There is no information about the file")
    if url is not None and object_path is not None:
        raise ValueError("It is unknown which of the files to take")

    url = url.replace(CDN_URL, CLOUD_API_URL)
    if url is not None and not url.startswith(CLOUD_API_URL):
        return False

    if object_path is not None:
        url = f"{CLOUD_API_URL}/{settings.BUCKET_NAME}/{object_path}"

    request = AWSRequest(method="DELETE", url=url)
    SigV4Auth(credentials, "s3", "ru-central1").add_auth(request)

    async with session.session.delete(
        url, headers=dict(request.headers)
    ) as response:
        if response.status >= 400:
            text = await response.text()
            raise Exception(f"Delete failed: {response.status} {text}")
        return True
