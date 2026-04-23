from app.core.config import settings
from app.core.errors import APIError, ErrorCode


def require_maintenance_api_enabled() -> None:
    if not settings.ENABLE_MAINTENANCE_API:
        raise APIError(ErrorCode.FORBIDDEN)
