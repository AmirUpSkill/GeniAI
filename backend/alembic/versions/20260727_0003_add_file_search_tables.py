"""add file search tables

Revision ID: 20260727_0003
Revises: 20260705_0002
Create Date: 2026-07-27 18:30:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260727_0003"
down_revision: str | None = "20260705_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "file_search_documents",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("chat_session_id", sa.String(), nullable=False),
        sa.Column("original_name", sa.String(length=512), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("gemini_store_name", sa.String(length=512), nullable=True),
        sa.Column("gemini_document_name", sa.String(length=512), nullable=True),
        sa.Column("gemini_operation_name", sa.String(length=512), nullable=True),
        sa.Column("failure_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("ready_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'indexing', 'ready', 'failed')",
            name="ck_file_search_documents_status",
        ),
        sa.ForeignKeyConstraint(
            ["chat_session_id"],
            ["chat_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "chat_session_id",
            name="uq_file_search_documents_chat_session_id",
        ),
    )
    op.create_index(
        op.f("ix_file_search_documents_chat_session_id"),
        "file_search_documents",
        ["chat_session_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_file_search_documents_status"),
        "file_search_documents",
        ["status"],
        unique=False,
    )

    op.create_table(
        "file_search_citations",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("message_id", sa.String(), nullable=False),
        sa.Column("document_id", sa.String(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("file_name", sa.String(length=512), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("source_excerpt", sa.Text(), nullable=False),
        sa.Column("media_id", sa.String(length=512), nullable=True),
        sa.Column("custom_metadata", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["file_search_documents.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["message_id"],
            ["chat_messages.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_file_search_citations_document_id"),
        "file_search_citations",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_file_search_citations_message_id"),
        "file_search_citations",
        ["message_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_file_search_citations_message_id"),
        table_name="file_search_citations",
    )
    op.drop_index(
        op.f("ix_file_search_citations_document_id"),
        table_name="file_search_citations",
    )
    op.drop_table("file_search_citations")
    op.drop_index(
        op.f("ix_file_search_documents_status"),
        table_name="file_search_documents",
    )
    op.drop_index(
        op.f("ix_file_search_documents_chat_session_id"),
        table_name="file_search_documents",
    )
    op.drop_table("file_search_documents")
