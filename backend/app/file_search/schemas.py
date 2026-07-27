from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

DocumentStatus = Literal["pending", "indexing", "ready", "failed"]


class FileSearchDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    chat_session_id: str = Field(serialization_alias="chatSessionId")
    original_name: str = Field(serialization_alias="originalName")
    content_type: str = Field(serialization_alias="contentType")
    size_bytes: int = Field(serialization_alias="sizeBytes")
    status: DocumentStatus
    failure_message: str | None = Field(default=None, serialization_alias="failureMessage")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")
    ready_at: datetime | None = Field(default=None, serialization_alias="readyAt")


class FileSearchDocumentResponse(BaseModel):
    success: bool = True
    data: FileSearchDocumentRead | None


class FileSearchCitationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    document_id: str = Field(serialization_alias="documentId")
    position: int
    file_name: str = Field(serialization_alias="fileName")
    page_number: int | None = Field(default=None, serialization_alias="pageNumber")
    source_excerpt: str = Field(serialization_alias="sourceExcerpt")
    media_id: str | None = Field(default=None, serialization_alias="mediaId")
    custom_metadata: dict[str, Any] | None = Field(
        default=None,
        serialization_alias="customMetadata",
    )


class FileSearchDeleteResponse(BaseModel):
    success: bool = True
    message: str

