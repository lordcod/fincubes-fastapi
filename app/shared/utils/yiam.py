import json
import jwt
import anyio
from datetime import datetime, timedelta, timezone

from app.shared.clients import session


EXT_TOKEN = timedelta(seconds=10 * 60)


class YandexIAM:
    IAM_URL = "https://iam.api.cloud.yandex.net/iam/v1/tokens"

    def __init__(self, key_path: str):
        self.key_path = key_path
        self.private_key = None
        self.key_id = None
        self.service_account_id = None
        self._iam_token = None
        self._expires_at = None

    async def _load_key(self):
        if self.private_key is None:
            async with await anyio.open_file(self.key_path, "r") as f:
                content = await f.read()
            obj = json.loads(content)
            self.private_key = obj["private_key"]
            self.key_id = obj["id"]
            self.service_account_id = obj["service_account_id"]

    async def _create_jwt(self) -> str:
        await self._load_key()
        now = datetime.now(timezone.utc)
        payload = {
            "aud": self.IAM_URL,
            "iss": self.service_account_id,
            "iat": now,
            "exp": now + EXT_TOKEN,
        }
        encoded_token = jwt.encode(
            payload,
            self.private_key,
            algorithm="PS256",
            headers={"kid": self.key_id},
        )
        return encoded_token

    async def _update_token(self):
        jwt_token = await self._create_jwt()
        async with session.session.post(self.IAM_URL, json={"jwt": jwt_token}) as resp:
            data = await resp.json()
            if resp.status != 200:
                raise RuntimeError(f"IAM error {resp.status}: {data}")
            self._iam_token = data["iamToken"]
            self._expires_at = datetime.fromisoformat(
                data["expiresAt"].replace("Z", "+00:00")
            )

    async def get_token(self) -> str:
        """Возвращает актуальный IAM-токен. Обновляет при необходимости."""
        if not self._iam_token or datetime.now(timezone.utc) >= self._expires_at:
            await self._update_token()
        return self._iam_token
