from jwtifypy import JWTConfig
from app.core.config import settings


def init_jwt():
    JWTConfig.init({
        "keys": {
            "alg": settings.ALGORITHM,
            "secret": settings.SECRET_KEY
        },
        "leeway": 1.0,
        "options": {
            "verify_sub": False,
            "strict_aud": False,
            "verify_aud": True,
            "verify_iss": True,
        }
    })
