from enum import Enum
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from dataclasses import dataclass

from fastapi.routing import APIRoute


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
        1003, "Попытки истекли, запросите код заново", 400)
    ALREADY_VERIFIED = ErrorInfo(1004, "Пользователь уже верифицирован", 400)
    INVALID_TOKEN = ErrorInfo(1005, "Неверный токен", 403)
    VERIFICATION_FAILED = ErrorInfo(
        1006, "Верификация не пройдена, пройдите её чтобы продолжить", 400)
    INCORRECT_CURRENT_PASSWORD = ErrorInfo(
        1007, "Неверный текущий пароль", 400)
    CAPTCHA_FAILED = ErrorInfo(1008, "Ошибка капчи", 400)

    # 2xxx — Пользователь / учётные данные
    USER_NOT_FOUND = ErrorInfo(2001, "Пользователь не найден", 404)
    EMAIL_ALREADY_TAKEN = ErrorInfo(2002, "Email уже занят", 400)
    INSUFFICIENT_PRIVILEGES = ErrorInfo(2003, "Недостаточно прав", 403)
    USER_ALREADY_HAS_ATHLETE = ErrorInfo(
        2004, "Пользователь уже имеет атлета", 400)
    ATHLETE_ALREADY_BOUND_TO_OTHER_USER = ErrorInfo(
        2005, "Атлет уже привязан к другому пользователю", 400)

    # 3xxx — Данные / ресурсы / бизнес-логика
    ATHLETE_NOT_FOUND = ErrorInfo(3001, "Атлет не найден", 404)
    COMPETITION_NOT_FOUND = ErrorInfo(3002, "Соревнование не найдено", 404)
    DISTANCE_NOT_FOUND = ErrorInfo(3003, "Дистанция не найдена", 404)
    RECORD_NOT_FOUND = ErrorInfo(3004, "Рекорд не найден", 404)
    RESULT_NOT_FOUND = ErrorInfo(3005, "Результат не найден", 404)
    SOME_DISTANCES_NOT_FOUND = ErrorInfo(
        3006, "Некоторые дистанции не найдены", 404)
    ATHLETE_COACH_RELATIONSHIP_NOT_FOUND = ErrorInfo(
        3007, "Связь атлета с тренером не найдена", 404)
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
        4001, "Не удалось отправить электронное письмо", 500)
    FILE_TOO_LARGE = ErrorInfo(4002, "Файл слишком большой", 413)
    RATE_LIMIT_EXCEEDED = ErrorInfo(4003, "Превышено количество запросов", 429)

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
        self.status_code = (error_code.http_status
                            if status_code is None
                            else status_code)
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
