import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import ApiError

logger = logging.getLogger(__name__)

HTTP_ERROR_CODES = {
    400: "bad_request",
    401: "authentication_required",
    403: "forbidden",
    404: "resource_not_found",
    405: "method_not_allowed",
}


def error_response(
    *,
    status_code: int,
    detail: str,
    code: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail, "code": code},
        headers=headers,
    )


async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    return error_response(
        status_code=exc.status_code,
        detail=exc.detail,
        code=exc.code,
        headers=exc.headers,
    )


async def validation_error_handler(_: Request, __: RequestValidationError) -> JSONResponse:
    return error_response(
        status_code=422,
        detail="Verifique os campos informados",
        code="validation_error",
    )


async def integrity_error_handler(_: Request, __: IntegrityError) -> JSONResponse:
    # This is a safe fallback. Known constraints should be translated into a
    # specific domain conflict close to the operation that identifies them.
    return error_response(
        status_code=409,
        detail="Conflito com dados existentes",
        code="data_integrity_conflict",
    )


async def http_error_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, str) else "Não foi possível processar a requisição"
    return error_response(
        status_code=exc.status_code,
        detail=detail,
        code=HTTP_ERROR_CODES.get(exc.status_code, "http_error"),
        headers=exc.headers,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unexpected error while processing %s %s",
        request.method,
        request.url.path,
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    return error_response(
        status_code=500,
        detail="Erro interno do servidor",
        code="internal_server_error",
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
