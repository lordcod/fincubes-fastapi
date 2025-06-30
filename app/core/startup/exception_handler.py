
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.errors import (APIError, api_error_handler,
                             http_exception_handler,
                             unhandled_exception_handler,
                             validation_exception_handler)


def add_exception_handler(app: FastAPI):
    app.add_exception_handler(APIError, api_error_handler)
    app.add_exception_handler(RequestValidationError,
                              validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
