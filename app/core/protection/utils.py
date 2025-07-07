import time
import json
import hashlib
from urllib.parse import urlparse

from jose.utils import base64url_encode
from jose import JWTError, jwt, jwk

from app.core.config import settings
from app.core.errors import APIError, ErrorCode


def is_same_normalized_path(htu: str, url: str) -> bool:
    """
    Сравнивает пути из HTU и URL с учетом нормализации конечного слэша.
    Возвращает True, если пути совпадают.
    """
    def normalize(path: str) -> str:
        if path != "/" and path.endswith("/"):
            return path[:-1]
        return path

    htu_path = normalize(urlparse(htu).path)
    url_path = normalize(urlparse(url).path)

    return htu_path == url_path


def verify_pow(server_nonce: str, nonce: str, fingerprint: str):
    h = hashlib.sha256(
        f"{server_nonce}:{nonce}:{fingerprint}".encode()
    ).hexdigest()
    if not h.startswith("0" * (settings.POW_BITS // 4)):
        raise APIError(ErrorCode.PROTECTION_INVALID_POW)


def jwk_thumbprint(jwk_pub: dict) -> str:
    """RFC 7638 thumbprint (base64url)"""
    canon = json.dumps({
        "crv": jwk_pub["crv"],
        "kty": jwk_pub["kty"],
        "x": jwk_pub["x"],
        "y": jwk_pub["y"]
    }, separators=(",", ":"), sort_keys=True).encode()
    return base64url_encode(hashlib.sha256(canon).digest()).decode()


def verify_dpop(method: str, url: str, dpop_jwt: str, jwk_pub: dict):
    try:
        header = jwt.get_unverified_header(dpop_jwt)
        alg = header["alg"]
        if jwk_pub != header['jwk']:
            raise APIError(ErrorCode.PROTECTION_INVALID_DPOP_HEADER)
        key = jwk.construct(jwk_pub, algorithm=alg)

        if header.get("typ") != "dpop+jwt":
            raise APIError(ErrorCode.PROTECTION_INVALID_DPOP_HEADER)

        payload = jwt.decode(dpop_jwt, key, algorithms=[alg])
        if payload["htm"] != method:
            raise APIError(ErrorCode.PROTECTION_INVALID_DPOP_HTM)

        if not is_same_normalized_path(payload["htu"], url):
            raise APIError(ErrorCode.PROTECTION_INVALID_DPOP_HTU)

        if abs(payload["iat"] - int(time.time())) > 3:
            raise APIError(ErrorCode.PROTECTION_INVALID_DPOP_IAT)

        return True
    except (JWTError, KeyError, TypeError, ValueError) as exc:
        raise APIError(ErrorCode.PROTECTION_BAD_DPOP) from exc
