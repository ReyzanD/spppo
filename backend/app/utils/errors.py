"""Uniform error envelope for every failure path (see docs/FRD.md §4.1).

Every error response has the shape:

    {"status": "error", "error": {"code": "...", "message": "..."}}

Routers and services raise ``AppError`` for expected failures; the handlers here
make sure even unexpected paths (unknown route, wrong method, unhandled
exception) still produce that envelope instead of leaking a traceback or a bare
``{"detail": ...}``.

Status codes are written as plain integers rather than ``fastapi.status``
constants: the 422/500 constants were renamed in Starlette 1.x, and the numbers
themselves never change.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

HTTP_422_UNPROCESSABLE = 422
HTTP_500_INTERNAL_ERROR = 500


class AppError(Exception):
    """An expected, client-facing failure."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


# Status code -> error.code fallback, used when the failure did not come from AppError.
_STATUS_CODE_MAP: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "TOKEN_INVALID",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    503: "MODEL_UNAVAILABLE",
}


def error_body(code: str, message: str, details: Any = None) -> dict[str, Any]:
    """Build the standard error envelope."""
    error: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return {"status": "error", "error": error}


def register_exception_handlers(app: FastAPI) -> None:
    """Attach handlers so every failure uses the envelope."""

    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=HTTP_422_UNPROCESSABLE,
            content=error_body(
                "VALIDATION_ERROR",
                "Data yang dikirim tidak valid",
                jsonable_encoder(exc.errors()),
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = _STATUS_CODE_MAP.get(exc.status_code, "HTTP_ERROR")
        message = exc.detail if isinstance(exc.detail, str) else "HTTP error"
        return JSONResponse(status_code=exc.status_code, content=error_body(code, message))

    @app.exception_handler(Exception)
    async def _unhandled_error(request: Request, _exc: Exception) -> JSONResponse:
        # Log the real cause, return a generic message: no internals to the client.
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=HTTP_500_INTERNAL_ERROR,
            content=error_body("INTERNAL_ERROR", "Terjadi kesalahan pada server"),
        )
