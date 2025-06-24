from dataclasses import dataclass
from enum import Enum
from typing import Optional

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import (HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED,
                              HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND,
                              HTTP_405_METHOD_NOT_ALLOWED,
                              HTTP_406_NOT_ACCEPTABLE,
                              HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                              HTTP_422_UNPROCESSABLE_ENTITY,
                              HTTP_429_TOO_MANY_REQUESTS,
                              HTTP_500_INTERNAL_SERVER_ERROR,
                              HTTP_503_SERVICE_UNAVAILABLE)


@dataclass(frozen=True)
class ErrorInfo:
    code: int
    message: str
    http_status: int = 400


class ErrorCode(Enum):
    # 1xxx — Аутентификация / авторизация
    INVALID_VERIFICATION_CODE = ErrorInfo(1001, "Неправильный код", 400)
    VERIFICATION_NOT_FOUND = ErrorInfo(
        1002, "Не найдена попытка верификации", 404)
    VERIFICATION_ATTEMPTS_EXPIRED = ErrorInfo(
        1003, "Попытки истекли, запросите код заново", 400
    )
    ALREADY_VERIFIED = ErrorInfo(1004, "Пользователь уже верифицирован", 400)
    INVALID_TOKEN = ErrorInfo(1005, "Неверный токен", 403)
    INVALID_TYPE_TOKEN = ErrorInfo(1006, "Неверный тип токена", 403)
    VERIFICATION_FAILED = ErrorInfo(
        1007, "Верификация не пройдена, пройдите её чтобы продолжить", 400
    )
    INCORRECT_CURRENT_PASSWORD = ErrorInfo(
        1008, "Неверный текущий пароль", 400)
    CAPTCHA_FAILED = ErrorInfo(1009, "Ошибка капчи", 400)
    EXPIRED_TOKEN = ErrorInfo(1010, "Срок действия токена истек", 403)
    VERIFICATION_EXPIRED = ErrorInfo(
        1002, "Срок действия подтверждения истек", 403)

    # 2xxx — Пользователь / учётные данные
    USER_NOT_FOUND = ErrorInfo(2001, "Пользователь не найден", 404)
    EMAIL_ALREADY_TAKEN = ErrorInfo(2002, "Email уже занят", 400)
    INSUFFICIENT_PRIVILEGES = ErrorInfo(2003, "Недостаточно прав", 403)
    USER_ALREADY_HAS_ATHLETE = ErrorInfo(
        2004, "Пользователь уже имеет атлета", 400)
    ATHLETE_ALREADY_BOUND_TO_OTHER_USER = ErrorInfo(
        2005, "Атлет уже привязан к другому пользователю", 400
    )

    # 3xxx — Данные / ресурсы / бизнес-логика
    ATHLETE_NOT_FOUND = ErrorInfo(3001, "Атлет не найден", 404)
    COMPETITION_NOT_FOUND = ErrorInfo(3002, "Соревнование не найдено", 404)
    DISTANCE_NOT_FOUND = ErrorInfo(3003, "Дистанция не найдена", 404)
    RECORD_NOT_FOUND = ErrorInfo(3004, "Рекорд не найден", 404)
    RESULT_NOT_FOUND = ErrorInfo(3005, "Результат не найден", 404)
    SOME_DISTANCES_NOT_FOUND = ErrorInfo(
        3006, "Некоторые дистанции не найдены", 404)
    ATHLETE_COACH_RELATIONSHIP_NOT_FOUND = ErrorInfo(
        3007, "Связь атлета с тренером не найдена", 404
    )
    INVALID_USER_ROLE = ErrorInfo(3008, "Неверный тип пользователя", 400)
    EMPTY_DATA = ErrorInfo(3009, "Пустые данные", 422)
    CLUB_CANNOT_BE_EMPTY = ErrorInfo(3010, "Клуб не может быть пустым", 422)
    ATHLETE_ALREADY_ADDED = ErrorInfo(
        3011, "Атлет уже добавлен в профиль", 400)
    STANDARD_NOT_FOUND = ErrorInfo(3012, "Стандарт не найден", 404)
    ATHLETE_COACH_NOT_FOUND = ErrorInfo(
        3013, "Связь с тренером не найдена", 404)
    ALREADY_ADDED_ATHLETE = ErrorInfo(3014, "Атлет уже добавлен", 400)
    INVALID_ROLE = ErrorInfo(3015, "Неверная роль", 403)

    # 4xxx — Внутренние ошибки / внешние сервисы
    SEND_EMAIL_EXCEPTION = ErrorInfo(
        4001, "Не удалось отправить электронное письмо", 500
    )
    FILE_TOO_LARGE = ErrorInfo(4002, "Файл слишком большой", 413)
    RATE_LIMIT_EXCEEDED = ErrorInfo(4003, "Превышено количество запросов", 429)

    # 5xxx — Ошибки Starlette / HTTP-протокола
    BAD_REQUEST = ErrorInfo(5000, "Некорректный запрос", HTTP_400_BAD_REQUEST)
    UNAUTHORIZED = ErrorInfo(5001, "Неавторизован", HTTP_401_UNAUTHORIZED)
    FORBIDDEN = ErrorInfo(5002, "Доступ запрещён", HTTP_403_FORBIDDEN)
    NOT_FOUND = ErrorInfo(5003, "Ресурс не найден", HTTP_404_NOT_FOUND)
    METHOD_NOT_ALLOWED = ErrorInfo(
        5004, "Метод не поддерживается", HTTP_405_METHOD_NOT_ALLOWED
    )
    NOT_ACCEPTABLE = ErrorInfo(
        5005, "Неприемлемый формат ответа", HTTP_406_NOT_ACCEPTABLE
    )
    UNSUPPORTED_MEDIA_TYPE = ErrorInfo(
        5006, "Неподдерживаемый тип данных", HTTP_415_UNSUPPORTED_MEDIA_TYPE
    )
    UNPROCESSABLE_ENTITY = ErrorInfo(
        5007, "Ошибка валидации данных", HTTP_422_UNPROCESSABLE_ENTITY
    )
    TOO_MANY_REQUESTS = ErrorInfo(
        5008, "Слишком много запросов", HTTP_429_TOO_MANY_REQUESTS
    )
    INTERNAL_SERVER_ERROR = ErrorInfo(
        5009, "Внутренняя ошибка сервера", HTTP_500_INTERNAL_SERVER_ERROR
    )
    SERVICE_UNAVAILABLE = ErrorInfo(
        5010, "Сервис временно недоступен", HTTP_503_SERVICE_UNAVAILABLE
    )

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
    def __init__(self, error_code: ErrorCode, status_code: Optional[int] = None):
        self.status_code = (
            error_code.http_status if status_code is None else status_code
        )
        self.error_code = error_code.code
        self.error_name = error_code.name
        self.message = error_code.message


error_map = {
    400: ErrorCode.BAD_REQUEST,
    401: ErrorCode.UNAUTHORIZED,
    403: ErrorCode.FORBIDDEN,
    404: ErrorCode.NOT_FOUND,
    405: ErrorCode.METHOD_NOT_ALLOWED,
    406: ErrorCode.NOT_ACCEPTABLE,
    415: ErrorCode.UNSUPPORTED_MEDIA_TYPE,
    422: ErrorCode.UNPROCESSABLE_ENTITY,
    429: ErrorCode.TOO_MANY_REQUESTS,
    500: ErrorCode.INTERNAL_SERVER_ERROR,
    503: ErrorCode.SERVICE_UNAVAILABLE,
}


async def api_error_handler(request: Request, exc: APIError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "error_name": exc.error_name,
            "message": exc.message,
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error = ErrorCode.UNPROCESSABLE_ENTITY
    return JSONResponse(
        status_code=error.http_status,
        content={
            "error_code": error.code,
            "error_name": error.name,
            "message": error.message,
            "details": exc.errors(),
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    error = error_map.get(exc.status_code, ErrorCode.INTERNAL_SERVER_ERROR)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": error.code,
            "error_name": error.name,
            "message": error.message,
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    error = ErrorCode.INTERNAL_SERVER_ERROR
    return JSONResponse(
        status_code=error.http_status,
        content={
            "error_code": error.code,
            "error_name": error.name,
            "message": error.message,
        },
    )
