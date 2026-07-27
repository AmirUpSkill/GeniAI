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


class ChatSessionNotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "CHAT_SESSION_NOT_FOUND"
    message = "Chat session was not found."


class AIProviderError(AppError):
    status_code = status.HTTP_502_BAD_GATEWAY
    code = "AI_PROVIDER_FAILED"
    message = "AI provider request failed."


class FileSearchDocumentNotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "FILE_SEARCH_DOCUMENT_NOT_FOUND"
    message = "The chat does not have an indexed document."


class FileSearchDocumentConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "FILE_SEARCH_DOCUMENT_EXISTS"
    message = "This chat already has a document. Remove it before uploading another."


class FileSearchDocumentNotReadyError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "FILE_SEARCH_DOCUMENT_NOT_READY"
    message = "The document is still being prepared. Try again when indexing is complete."


class FileSearchUploadError(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    code = "FILE_SEARCH_UPLOAD_INVALID"
    message = "The uploaded document is not supported."


class FileSearchProviderError(AppError):
    status_code = status.HTTP_502_BAD_GATEWAY
    code = "FILE_SEARCH_PROVIDER_FAILED"
    message = "Gemini could not process the document."


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
