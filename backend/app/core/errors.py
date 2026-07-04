from dataclasses import dataclass

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


@dataclass(frozen=True)
class ErrorDetail:
    code: str
    message: str


class AppError(Exception):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "APP_ERROR"
    message = "Application error."

    def __init__(self, message: str | None = None, code: str | None = None) -> None:
        self.detail = ErrorDetail(
            code=code or self.code,
            message=message or self.message,
        )


class AuthUnauthorizedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "AUTH_UNAUTHORIZED"
    message = "User is not authenticated."


class AuthProviderError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "AUTH_PROVIDER_FAILED"
    message = "Google authentication failed."


def app_error_response(error: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={
            "success": False,
            "error": {
                "code": error.detail.code,
                "message": error.detail.message,
            },
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
        return app_error_response(exc)
