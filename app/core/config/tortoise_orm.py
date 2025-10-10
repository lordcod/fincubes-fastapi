from app.core.config import settings
try:
    import aerich
except ImportError:
    _aerich_found = False
else:
    _aerich_found = True

TORTOISE_ORM = {
    "connections": {
        "default": settings.DATABASE_URL,
    },
    "apps": {
        "models": {
            "models": list(filter(bool, [
                "app.models",
                "aerich.models" if _aerich_found else None,
            ])),
            "default_connection": "default",
        },
    },
    "use_tz": True,
    "timezone": "UTC",
}
