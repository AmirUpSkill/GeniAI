from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.chat_message import ChatMessage


class FileSearchDocument(Base):
    """
        The durable Gemini resources created for one chat document.
    A chat document is a file uploaded by the user.

    Geni deliberately does not persist the original file in this first version.
    The database keeps only display metadata and the Gemini resource names needed
    to search or delete the indexed document.
    """

    __tablename__ = "file_search_documents"
    __table_args__ = (
        UniqueConstraint("chat_session_id", name="uq_file_search_documents_chat_session_id"),
        CheckConstraint(
            "status IN ('pending', 'indexing', 'ready', 'failed')",
            name="ck_file_search_documents_status",
        ),
    )

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: f"doc_{uuid4().hex}",
    )
    chat_session_id: Mapped[str] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_name: Mapped[str] = mapped_column(String(length=512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(length=128), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(length=24),
        nullable=False,
        default="pending",
        index=True,
    )
    gemini_store_name: Mapped[str | None] = mapped_column(String(length=512), nullable=True)
    gemini_document_name: Mapped[str | None] = mapped_column(String(length=512), nullable=True)
    gemini_operation_name: Mapped[str | None] = mapped_column(String(length=512), nullable=True)
    failure_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    citations: Mapped[list[FileSearchCitation]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )


class FileSearchCitation(Base):
    """
    A source passage returned with one grounded assistant message.
    A citation is a source passage returned with one grounded assistant message.
    """

    __tablename__ = "file_search_citations"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: f"cite_{uuid4().hex}",
    )
    message_id: Mapped[str] = mapped_column(
        ForeignKey("chat_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[str] = mapped_column(
        ForeignKey("file_search_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    file_name: Mapped[str] = mapped_column(String(length=512), nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    media_id: Mapped[str | None] = mapped_column(String(length=512), nullable=True)
    custom_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    message: Mapped[ChatMessage] = relationship(back_populates="file_search_citations")
    document: Mapped[FileSearchDocument] = relationship(back_populates="citations")

