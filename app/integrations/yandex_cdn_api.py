from typing import List, Literal
from app.core.config import settings
from app.shared.clients import session
from app.shared.utils.yiam import YandexIAM

yandex_iam = YandexIAM("yandex-secret-key.json")
CDN_BASE_URL = f"https://cdn.api.cloud.yandex.net/cdn/v1/cache/{settings.YANDEX_CDN_RESOURCE_ID}"


async def update_cdn_cache(
    paths: List[str] | str,
    action: Literal['purge', 'prefetch'] = "purge"
) -> bool:
    """
    Universal function to purge or prefetch CDN cache.

    Args:
        paths: A single path or a list of paths for the action.
        action: The type of action: "purge" to clear the cache, "prefetch" to preload it.

    Returns:
        bool: True if the request was successful, otherwise False.
    """
    if action not in ("purge", "prefetch"):
        raise ValueError('Action must be "purge" or "prefetch".')

    url = f"{CDN_BASE_URL}:{action}"
    token = await yandex_iam.get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {"paths": paths if isinstance(paths, list) else [paths]}

    async with session.session.post(url, headers=headers, json=payload) as response:
        return response.ok
