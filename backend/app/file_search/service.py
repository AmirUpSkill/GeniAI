from app.ai.provider import FileCitation
from app.core.errors import (
    ChatSessionNotFoundError,
    FileSearchDocumentConflictError,
    FileSearchDocumentNotFoundError,
    FileSearchDocumentNotReadyError,
)
from app.file_search.gemini import GeminiFileSearchGateway
from app.file_search.models import FileSearchDocument
from app.file_search.repository import FileSearchRepository
from app.models.chat_message import ChatMessage
from app.models.user import User


class FileSearchService:
    """
        Service layer for the file search feature.
    """
    def __init__(
        self,
        repository: FileSearchRepository,
        gateway: GeminiFileSearchGateway,
    ) -> None:
        self.repository = repository
        self.gateway = gateway

    async def create_pending_document(
        self,
        current_user: User,
        chat_session_id: str,
        *,
        original_name: str,
        content_type: str,
        size_bytes: int,
    ) -> FileSearchDocument:
        await self._require_owned_chat(current_user.id, chat_session_id)
        existing = await self.repository.get_document_for_chat(chat_session_id)
        if existing is not None:
            raise FileSearchDocumentConflictError()

        document = await self.repository.create_document(
            chat_session_id,
            original_name,
            content_type,
            size_bytes,
        )
        await self.repository.session.commit()
        return document

    async def get_document(
        self,
        current_user: User,
        chat_session_id: str,
    ) -> FileSearchDocument | None:
        await self._require_owned_chat(current_user.id, chat_session_id)
        return await self.repository.get_document_for_chat(chat_session_id)

    async def get_ready_document(
        self,
        current_user: User,
        chat_session_id: str,
    ) -> FileSearchDocument | None:
        document = await self.get_document(current_user, chat_session_id)
        if document is None:
            return None
        if document.status in {"pending", "indexing"}:
            raise FileSearchDocumentNotReadyError()
        if document.status == "failed":
            raise FileSearchDocumentNotReadyError(
                "Document indexing failed. Remove it and upload the PDF again."
            )
        if not document.gemini_store_name:
            raise FileSearchDocumentNotReadyError(
                "The indexed document is missing its Gemini store."
            )
        return document

    async def delete_document(
        self,
        current_user: User,
        chat_session_id: str,
    ) -> None:
        await self._require_owned_chat(current_user.id, chat_session_id)
        document = await self.repository.get_document_for_chat(chat_session_id)
        if document is None:
            raise FileSearchDocumentNotFoundError()
        if document.status in {"pending", "indexing"}:
            raise FileSearchDocumentNotReadyError(
                "Wait for indexing to finish before removing this document."
            )
        await self._delete_document_resources(document)

    async def delete_for_chat_session_if_present(
        self,
        current_user: User,
        chat_session_id: str,
    ) -> None:
        document = await self.repository.get_document_for_chat(chat_session_id)
        if document is not None:
            if document.status in {"pending", "indexing"}:
                raise FileSearchDocumentNotReadyError(
                    "Wait for indexing to finish before deleting this chat."
                )
            await self._delete_document_resources(document)

    async def save_citations(
        self,
        assistant_message: ChatMessage,
        document: FileSearchDocument,
        citations: list[FileCitation],
    ) -> None:
        for position, citation in enumerate(citations, start=1):
            await self.repository.create_citation(
                message_id=assistant_message.id,
                document_id=document.id,
                position=position,
                file_name=citation.file_name or document.original_name,
                page_number=citation.page_number,
                source_excerpt=citation.source_excerpt,
                media_id=citation.media_id,
                custom_metadata=citation.custom_metadata,
            )

    async def _delete_document_resources(self, document: FileSearchDocument) -> None:
        if document.gemini_store_name:
            await self.gateway.delete_store(document.gemini_store_name)
        await self.repository.delete_document(document)
        await self.repository.session.commit()

    async def _require_owned_chat(self, user_id: str, chat_session_id: str) -> None:
        chat_session = await self.repository.get_owned_chat_session(user_id, chat_session_id)
        if chat_session is None:
            raise ChatSessionNotFoundError()
