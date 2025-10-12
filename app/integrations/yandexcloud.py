import hashlib
from typing import Optional
from urllib.parse import urlparse

from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials

from app.core.config import settings
from app.shared.clients import session

credentials = Credentials(settings.AWS_KEY_ID, settings.AWS_SECRET_KEY)

CLOUD_API_URL = "https://storage.yandexcloud.net"
CDN_URL = "https://cdn.fincubes.ru"

_CLOUD_NETLOC = urlparse(CLOUD_API_URL).netloc
_CDN_NETLOC = urlparse(CDN_URL).netloc


class CloudError(Exception):
    """Ошибка при работе с облачным хранилищем."""


def make_cloud_url(object_path: str) -> str:
    """Собрать прямой URL для работы с S3."""
    return f"{CLOUD_API_URL}/{settings.BUCKET_NAME}/{object_path}"


def make_cdn_url(object_path: str) -> str:
    """Собрать публичный CDN-URL."""
    return f"{CDN_URL}/{object_path}"


def extract_object_path(url: str) -> Optional[str]:
    """
    Получить object_path из cdn/cloud URL.
    Вернёт None, если url не подходит.
    """
    parsed = urlparse(url)

    if parsed.netloc == _CDN_NETLOC:
        return parsed.path.lstrip("/")

    if parsed.netloc == _CLOUD_NETLOC:
        parts = parsed.path.lstrip("/").split("/", 1)
        if len(parts) > 1 and parts[0] == settings.BUCKET_NAME:
            return parts[1]

    return None


async def cloud_request(
    method: str,
    object_path: str,
    data: Optional[bytes] = None,
) -> None:
    """Выполнить авторизованный запрос к S3."""
    url = make_cloud_url(object_path)
    request = AWSRequest(method=method, url=url, data=data)

    if data is not None:
        body_hash = hashlib.sha256(data).hexdigest()
        request.headers["x-amz-content-sha256"] = body_hash

    SigV4Auth(credentials, "s3", "ru-central1").add_auth(request)

    async with session.session.request(method.upper(), url, data=data, headers=dict(request.headers)) as response:
        if response.status >= 400:
            text = await response.text()
            raise CloudError(f"{method} failed: {response.status} {text}")


async def upload_file(body: bytes, object_path: str) -> str:
    """Загрузить файл и вернуть CDN-URL."""
    await cloud_request("PUT", object_path, data=body)
    return make_cdn_url(object_path)


async def delete_file(*, url: Optional[str] = None, object_path: Optional[str] = None) -> bool:
    """Удалить файл из бакета."""
    if url is None and object_path is None:
        raise ValueError("Either url or object_path must be provided")
    if url is not None and object_path is not None:
        raise ValueError("Provide only one of url or object_path")

    if object_path is None:
        object_path = extract_object_path(url)
        if object_path is None:
            return False

    await cloud_request("DELETE", object_path)
    return True


async def copy_file(
    source_path: Optional[str] = None,
    target_path: Optional[str] = None,
    source_url: Optional[str] = None,
    target_url: Optional[str] = None,
) -> str:
    """
    Скопировать объект внутри S3-хранилища.
    Можно передавать пути или URL.
    Возвращает CDN-URL нового (целевого) объекта.
    """
    if source_path is not None and source_url is not None:
        raise ValueError("Provide only one of source_path or source_url")
    if target_path is not None and target_url is not None:
        raise ValueError("Provide only one of target_path or target_url")

    if source_path is None:
        if source_url is None:
            raise ValueError(
                "Either source_path or source_url must be provided")
        source_path = extract_object_path(source_url)
        if source_path is None:
            raise CloudError(
                f"Cannot extract object path from source_url: {source_url}")

    if target_path is None:
        if target_url is None:
            raise ValueError(
                "Either target_path or target_url must be provided")
        target_path = extract_object_path(target_url)
        if target_path is None:
            raise CloudError(
                f"Cannot extract object path from target_url: {target_url}")

    url = make_cloud_url(target_path)

    request = AWSRequest(
        method="PUT",
        url=url,
        headers={"x-amz-copy-source": f"/{settings.BUCKET_NAME}/{source_path}"}
    )

    SigV4Auth(credentials, "s3", "ru-central1").add_auth(request)

    async with session.session.put(url, headers=dict(request.headers)) as response:
        if response.status >= 400:
            text = await response.text()
            raise CloudError(f"Copy failed: {response.status} {text}")

    return make_cdn_url(target_path)


async def rename_file(
    source_path: Optional[str] = None,
    target_path: Optional[str] = None,
    source_url: Optional[str] = None,
    target_url: Optional[str] = None,
) -> str:
    """
    Переименовать объект (копирование + удаление исходного).
    Можно передавать пути или URL.
    Возвращает CDN-URL нового объекта.
    """
    new_url = await copy_file(
        source_path=source_path,
        target_path=target_path,
        source_url=source_url,
        target_url=target_url,
    )

    if source_path is None:
        if source_url is None:
            raise ValueError(
                "Either source_path or source_url must be provided")
        source_path = extract_object_path(source_url)
        if source_path is None:
            raise CloudError(
                f"Cannot extract object path from source_url: {source_url}")
    await delete_file(object_path=source_path)
    return new_url
