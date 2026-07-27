from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile, status

from app.auth.dependencies import get_current_user
from app.core.config import Settings, get_settings
from app.core.errors import FileSearchUploadError
from app.file_search.dependencies import get_file_search_service
from app.file_search.schemas import (
    FileSearchDeleteResponse,
    FileSearchDocumentRead,
    FileSearchDocumentResponse,
)
from app.file_search.service import FileSearchService
from app.file_search.tasks import index_document_in_background
from app.models.user import User

router = APIRouter(prefix="/chat/sessions", tags=["file-search"])

PDF_CONTENT_TYPES = {"application/pdf", "application/x-pdf"}


@router.post(
    "/{chat_session_id}/document",
    response_model=FileSearchDocumentResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_document(
    chat_session_id: str,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    file_search_service: Annotated[FileSearchService, Depends(get_file_search_service)],
    settings: Annotated[Settings, Depends(get_settings)],
    file: Annotated[UploadFile, File(description="One PDF document to index")],
) -> FileSearchDocumentResponse:
    original_name = (file.filename or "document.pdf").strip()
    content_type = (file.content_type or "").lower()

    if content_type not in PDF_CONTENT_TYPES or not original_name.lower().endswith(".pdf"):
        raise FileSearchUploadError("For now, Geni File Search accepts one PDF document.")

    file_bytes = await file.read(settings.file_search_max_file_bytes + 1)
    await file.close()

    if len(file_bytes) == 0:
        raise FileSearchUploadError("The selected PDF is empty.")
    if len(file_bytes) > settings.file_search_max_file_bytes:
        max_megabytes = settings.file_search_max_file_bytes // (1024 * 1024)
        raise FileSearchUploadError(f"The PDF must be {max_megabytes} MB or smaller.")
    if not file_bytes.startswith(b"%PDF-"):
        raise FileSearchUploadError("The selected file is not a valid PDF.")

    document = await file_search_service.create_pending_document(
        current_user,
        chat_session_id,
        original_name=original_name,
        content_type="application/pdf",
        size_bytes=len(file_bytes),
    )
    background_tasks.add_task(
        index_document_in_background,
        document_id=document.id,
        original_name=original_name,
        content_type="application/pdf",
        file_bytes=file_bytes,
        settings=settings,
    )
    return FileSearchDocumentResponse(data=FileSearchDocumentRead.model_validate(document))


@router.get(
    "/{chat_session_id}/document",
    response_model=FileSearchDocumentResponse,
)
async def get_document(
    chat_session_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    file_search_service: Annotated[FileSearchService, Depends(get_file_search_service)],
) -> FileSearchDocumentResponse:
    document = await file_search_service.get_document(current_user, chat_session_id)
    data = FileSearchDocumentRead.model_validate(document) if document is not None else None
    return FileSearchDocumentResponse(data=data)


@router.delete(
    "/{chat_session_id}/document",
    response_model=FileSearchDeleteResponse,
)
async def delete_document(
    chat_session_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    file_search_service: Annotated[FileSearchService, Depends(get_file_search_service)],
) -> FileSearchDeleteResponse:
    await file_search_service.delete_document(current_user, chat_session_id)
    return FileSearchDeleteResponse(message="File Search document deleted successfully.")

