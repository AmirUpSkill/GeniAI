# File Search module

This package owns the chat-scoped Gemini File Search feature.

## Responsibilities

- `routes.py` validates one PDF upload and exposes document lifecycle endpoints.
- `service.py` contains ownership, one-document-per-chat, readiness, and cleanup rules.
- `repository.py` is the only database access layer for documents and citations.
- `gemini.py` isolates Gemini store creation, upload, polling, and deletion.
- `tasks.py` performs indexing outside the request/response path.
- `models.py` persists Gemini resource names, status, and citation excerpts.
- `schemas.py` defines the public API payloads.

## Deliberate first-version limitation

Geni does **not** persist the original PDF. The upload is held in memory only while
the background task sends it to Gemini. After indexing, Geni stores:

- the original display name and size;
- the Gemini File Search store and document resource names;
- the indexing status; and
- citation excerpts/page numbers returned with grounded answers.

Because there is no retained source file, the citation dialog can show the exact
retrieved passage and page number but cannot render the original PDF page.

The lightweight FastAPI background task is also not restart-safe. Moving
`index_document_in_background` to a durable worker is the natural production
upgrade; the routes and database model can remain unchanged.

## Lifecycle

```text
pending -> indexing -> ready
                    -> failed
```

An indexing document cannot be deleted. This prevents its in-memory task from
finishing after the database row has disappeared and orphaning a Gemini store.
