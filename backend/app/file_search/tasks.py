from app.core.config import Settings
from app.db.session import AsyncSessionLocal
from app.file_search.gemini import GeminiFileSearchGateway
from app.file_search.repository import FileSearchRepository


async def index_document_in_background(
    *,
    document_id: str,
    original_name: str,
    content_type: str,
    file_bytes: bytes,
    settings: Settings,
) -> None:
    """
        Index an in-memory upload and persist only Gemini resource names.

    This lightweight background task is intentional for the first version. The
    bytes disappear when the task finishes, so a process restart during indexing
    cannot resume the upload. A durable queue can replace this function later
    without changing the public API or database model.
    """

    gateway = GeminiFileSearchGateway(settings)

    async with AsyncSessionLocal() as session:
        repository = FileSearchRepository(session)
        document = await repository.get_document_by_id(document_id)
        if document is None:
            return

        try:
            await repository.mark_processing(document)
            await session.commit()
            indexed = await gateway.create_and_index(
                document_id=document.id,
                display_name=original_name,
                content_type=content_type,
                file_bytes=file_bytes,
            )
            await repository.mark_indexing(
                document,
                indexed.store_name,
                indexed.operation_name,
            )
            await repository.mark_ready(document, indexed.document_name)
            await session.commit()
        except Exception as exc:
            await session.rollback()
            document = await repository.get_document_by_id(document_id)
            if document is None:
                return
            await repository.mark_failed(document, str(exc) or "Document indexing failed.")
            await session.commit()
