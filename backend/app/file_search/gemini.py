import asyncio
from dataclasses import dataclass
from io import BytesIO

from google import genai

from app.core.config import Settings
from app.core.errors import FileSearchProviderError


@dataclass(frozen=True)
class IndexedGeminiDocument:
    """
        Resource names returned after Gemini finishes indexing a document.4
    """
    store_name: str
    document_name: str | None
    operation_name: str | None


class GeminiFileSearchGateway:
    """
        Small boundary around the Gemini File Search lifecycle.

    Keeping provider-specific calls here prevents upload and polling details from
    leaking into HTTP routes, database repositories, or the chat feature.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _client(self) -> genai.Client:
        if self.settings.gemini_api_key.strip() == "":
            raise FileSearchProviderError("Gemini API key is not configured.")
        return genai.Client(api_key=self.settings.gemini_api_key)

    async def create_and_index(
        self,
        *,
        document_id: str,
        display_name: str,
        content_type: str,
        file_bytes: bytes,
    ) -> IndexedGeminiDocument:
        client = self._client()
        store_name: str | None = None

        try:
            store = await client.aio.file_search_stores.create(
                config={
                    "display_name": f"geni-{document_id}",
                    "embedding_model": self.settings.file_search_embedding_model,
                }
            )
            if not store.name:
                raise FileSearchProviderError(
                    "Gemini created a File Search store without a resource name."
                )
            store_name = store.name

            operation = await client.aio.file_search_stores.upload_to_file_search_store(
                file=BytesIO(file_bytes),
                file_search_store_name=store_name,
                config={
                    "display_name": display_name,
                    "mime_type": content_type,
                },
            )
            operation_name = operation.name

            while not operation.done:
                await asyncio.sleep(self.settings.file_search_poll_seconds)
                operation = await client.aio.operations.get(operation)

            if operation.error:
                raise FileSearchProviderError(
                    f"Gemini indexing failed: {operation.error}"
                )

            document_name = (
                operation.response.document_name if operation.response is not None else None
            )
            return IndexedGeminiDocument(
                store_name=store_name,
                document_name=document_name,
                operation_name=operation_name,
            )
        except FileSearchProviderError:
            if store_name is not None:
                await self._delete_store_quietly(client, store_name)
            raise
        except Exception as exc:
            if store_name is not None:
                await self._delete_store_quietly(client, store_name)
            raise FileSearchProviderError() from exc

    async def delete_store(self, store_name: str) -> None:
        client = self._client()
        try:
            await client.aio.file_search_stores.delete(
                name=store_name,
                config={"force": True},
            )
        except Exception as exc:
            raise FileSearchProviderError(
                "Gemini could not delete the File Search store."
            ) from exc

    async def _delete_store_quietly(self, client: genai.Client, store_name: str) -> None:
        try:
            await client.aio.file_search_stores.delete(
                name=store_name,
                config={"force": True},
            )
        except Exception:
            # Cleanup should not hide the original indexing error.
            return

