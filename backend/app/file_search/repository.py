from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.file_search.models import FileSearchCitation, FileSearchDocument
from app.models.chat_session import ChatSession


class FileSearchRepository:
    """
        Database access for documents and the citations produced from them.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_owned_chat_session(
        self,
        user_id: str,
        chat_session_id: str,
    ) -> ChatSession | None:
        result = await self.session.execute(
            select(ChatSession).where(
                ChatSession.id == chat_session_id,
                ChatSession.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_document(
        self,
        chat_session_id: str,
        original_name: str,
        content_type: str,
        size_bytes: int,
    ) -> FileSearchDocument:
        document = FileSearchDocument(
            chat_session_id=chat_session_id,
            original_name=original_name,
            content_type=content_type,
            size_bytes=size_bytes,
            status="pending",
        )
        self.session.add(document)
        await self.session.flush()
        await self.session.refresh(document)
        return document

    async def get_document_for_chat(
        self,
        chat_session_id: str,
    ) -> FileSearchDocument | None:
        result = await self.session.execute(
            select(FileSearchDocument).where(
                FileSearchDocument.chat_session_id == chat_session_id
            )
        )
        return result.scalar_one_or_none()

    async def get_document_by_id(self, document_id: str) -> FileSearchDocument | None:
        result = await self.session.execute(
            select(FileSearchDocument).where(FileSearchDocument.id == document_id)
        )
        return result.scalar_one_or_none()

    async def mark_indexing(
        self,
        document: FileSearchDocument,
        store_name: str,
        operation_name: str | None,
    ) -> None:
        document.status = "indexing"
        document.gemini_store_name = store_name
        document.gemini_operation_name = operation_name
        document.failure_message = None
        document.updated_at = datetime.now(UTC)
        await self.session.flush()

    async def mark_processing(self, document: FileSearchDocument) -> None:
        document.status = "indexing"
        document.failure_message = None
        document.updated_at = datetime.now(UTC)
        await self.session.flush()

    async def mark_ready(
        self,
        document: FileSearchDocument,
        gemini_document_name: str | None,
    ) -> None:
        now = datetime.now(UTC)
        document.status = "ready"
        document.gemini_document_name = gemini_document_name
        document.failure_message = None
        document.ready_at = now
        document.updated_at = now
        await self.session.flush()

    async def mark_failed(self, document: FileSearchDocument, message: str) -> None:
        document.status = "failed"
        document.failure_message = message[:2000]
        document.updated_at = datetime.now(UTC)
        await self.session.flush()

    async def delete_document(self, document: FileSearchDocument) -> None:
        await self.session.delete(document)
        await self.session.flush()

    async def create_citation(
        self,
        *,
        message_id: str,
        document_id: str,
        position: int,
        file_name: str,
        page_number: int | None,
        source_excerpt: str,
        media_id: str | None,
        custom_metadata: dict[str, object] | None,
    ) -> FileSearchCitation:
        citation = FileSearchCitation(
            message_id=message_id,
            document_id=document_id,
            position=position,
            file_name=file_name,
            page_number=page_number,
            source_excerpt=source_excerpt,
            media_id=media_id,
            custom_metadata=custom_metadata,
        )
        self.session.add(citation)
        await self.session.flush()
        return citation

    async def delete_citations_for_message(self, message_id: str) -> None:
        await self.session.execute(
            delete(FileSearchCitation).where(FileSearchCitation.message_id == message_id)
        )
