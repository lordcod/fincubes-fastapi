from enum import Enum

from fastapi import Request
from fastapi.responses import JSONResponse
from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorInfo:
    code: int
    message: str
    http_status: int = 400


class ErrorCode(Enum):
    ALREADY_VERIFIED = ErrorInfo(1001, "Пользователь уже верифицирован")
    VERIFICATION_NOT_FOUND = ErrorInfo(1002, "Не найдена попытка верификации")
    INVALID_VERIFICATION_CODE = ErrorInfo(1003, "Неправильный код")
    VERIFICATION_ATTEMPTS_EXPIRED = ErrorInfo(
        1004, "Попытки истекли, запросите код заново"
    )
    SEND_EMAIL_EXCEPTION = ErrorInfo(
        4001, "Не удалось отправить электронное письмо"
    )
    INVALID_TOKEN = ErrorInfo(1005, "Invalid token", 403)
    USER_NOT_FOUND = ErrorInfo(1006, "User not found", 403)
    INSUFFICIENT_PRIVILEGES = ErrorInfo(1007, "Insufficient privileges", 403)
    INVALID_ROLE = ErrorInfo(1008, "The user does not need a role")
    ALREADY_ADDED_ATHLETE = ErrorInfo(
        1009, "The athlete has already been added to your profile")

    @property
    def code(self):
        return self.value.code

    @property
    def message(self):
        return self.value.message

    @property
    def http_status(self):
        return self.value.http_status


class APIError(Exception):
    def __init__(self, error_code: ErrorCode, status_code: int = 400):
        self.status_code = status_code
        self.error_code = error_code.code
        self.error_name = error_code.name
        self.message = error_code.message


async def api_error_handler(request: Request, exc: APIError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "error_name": exc.error_name,
            "message": exc.message,
        }
    )
