import hashlib
from typing import Optional
from services import s3_session
from config import AWS_KEY_ID, AWS_SECRET_KEY, BUCKET_NAME
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials

credentials = Credentials(AWS_KEY_ID, AWS_SECRET_KEY)


async def upload_file(body: bytes, object_path: str):
    url = f"https://storage.yandexcloud.net/{BUCKET_NAME}/{object_path}"

    body_hash = hashlib.sha256(body).hexdigest()

    request = AWSRequest(method="PUT", url=url, data=body)
    request.headers["x-amz-content-sha256"] = body_hash
    SigV4Auth(credentials, "s3", "ru-central1").add_auth(request)

    async with s3_session.session.put(
        url, data=body, headers=dict(request.headers)
    ) as response:
        if response.status >= 400:
            text = await response.text()
            raise Exception(f"Upload failed: {response.status} {text}")
        return url


async def delete_file(*, url: Optional[str] = None, object_path: Optional[str] = None):
    if url is None and object_path is None:
        raise ValueError("There is no information about the file")
    if url is not None and object_path is not None:
        raise ValueError("It is unknown which of the files to take")

    if url is not None and not url.startswith("https://storage.yandexcloud.net/"):
        return False

    if object_path is not None:
        url = f"https://storage.yandexcloud.net/{BUCKET_NAME}/{object_path}"

    request = AWSRequest(method="DELETE", url=url)
    SigV4Auth(credentials, "s3", "ru-central1").add_auth(request)

    async with s3_session.session.delete(
        url, headers=dict(request.headers)
    ) as response:
        if response.status >= 400:
            text = await response.text()
            raise Exception(f"Delete failed: {response.status} {text}")
        return True
