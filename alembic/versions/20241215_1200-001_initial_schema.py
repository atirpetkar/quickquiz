"""Initial schema with documents, chunks, and questions tables

Revision ID: 001
Revises:
Create Date: 2024-12-15 12:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Create documents table
    op.create_table(
        "documents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(50), nullable=False),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("metadata_", sa.JSON(), nullable=True),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column("character_count", sa.Integer(), nullable=True),
        sa.Column(
            "processing_status", sa.String(50), nullable=False, server_default="pending"
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    # Create chunks table
    op.create_table(
        "chunks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("start_char", sa.Integer(), nullable=True),
        sa.Column("end_char", sa.Integer(), nullable=True),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column("embedding", postgresql.ARRAY(sa.Float), nullable=True),
        sa.Column("embedding_model", sa.String(100), nullable=True),
        sa.Column("metadata_", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
    )

    # Create questions table
    op.create_table(
        "questions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_ids", postgresql.ARRAY(postgresql.UUID), nullable=False),
        sa.Column(
            "question_type",
            sa.String(50),
            nullable=False,
            server_default="multiple_choice",
        ),
        sa.Column("difficulty", sa.String(20), nullable=False),
        sa.Column("bloom_level", sa.String(20), nullable=False),
        sa.Column("stem", sa.Text(), nullable=False),
        sa.Column("options", sa.JSON(), nullable=False),
        sa.Column("correct_answer", sa.String(10), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("distractors_explanation", sa.Text(), nullable=True),
        sa.Column("topic", sa.String(200), nullable=True),
        sa.Column("learning_objective", sa.Text(), nullable=True),
        sa.Column("source_content", sa.Text(), nullable=True),
        sa.Column("generation_prompt", sa.Text(), nullable=True),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("generation_metadata", sa.JSON(), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("evaluation_feedback", sa.JSON(), nullable=True),
        sa.Column("is_approved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
    )

    # Create indexes for performance
    op.create_index("idx_documents_status", "documents", ["processing_status"])
    op.create_index("idx_documents_content_type", "documents", ["content_type"])
    op.create_index("idx_documents_created_at", "documents", ["created_at"])

    op.create_index("idx_chunks_document_id", "chunks", ["document_id"])
    op.create_index(
        "idx_chunks_document_chunk", "chunks", ["document_id", "chunk_index"]
    )

    op.create_index("idx_questions_document_id", "questions", ["document_id"])
    op.create_index("idx_questions_difficulty", "questions", ["difficulty"])
    op.create_index("idx_questions_bloom_level", "questions", ["bloom_level"])
    op.create_index("idx_questions_quality_score", "questions", ["quality_score"])
    op.create_index("idx_questions_approved", "questions", ["is_approved"])
    op.create_index("idx_questions_topic", "questions", ["topic"])
    op.create_index("idx_questions_created_at", "questions", ["created_at"])

    # Create GIN index for JSON columns
    op.create_index(
        "idx_documents_metadata_gin", "documents", ["metadata_"], postgresql_using="gin"
    )
    op.create_index(
        "idx_chunks_metadata_gin", "chunks", ["metadata_"], postgresql_using="gin"
    )
    op.create_index(
        "idx_questions_options_gin", "questions", ["options"], postgresql_using="gin"
    )
    op.create_index(
        "idx_questions_metadata_gin",
        "questions",
        ["generation_metadata"],
        postgresql_using="gin",
    )

    # Create updated_at triggers
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """
    )

    op.execute(
        """
        CREATE TRIGGER update_documents_updated_at
        BEFORE UPDATE ON documents
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """
    )

    op.execute(
        """
        CREATE TRIGGER update_chunks_updated_at
        BEFORE UPDATE ON chunks
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """
    )

    op.execute(
        """
        CREATE TRIGGER update_questions_updated_at
        BEFORE UPDATE ON questions
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """
    )


def downgrade() -> None:
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_questions_updated_at ON questions")
    op.execute("DROP TRIGGER IF EXISTS update_chunks_updated_at ON chunks")
    op.execute("DROP TRIGGER IF EXISTS update_documents_updated_at ON documents")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")

    # Drop indexes
    op.drop_index("idx_questions_metadata_gin", "questions")
    op.drop_index("idx_questions_options_gin", "questions")
    op.drop_index("idx_chunks_metadata_gin", "chunks")
    op.drop_index("idx_documents_metadata_gin", "documents")
    op.drop_index("idx_questions_created_at", "questions")
    op.drop_index("idx_questions_topic", "questions")
    op.drop_index("idx_questions_approved", "questions")
    op.drop_index("idx_questions_quality_score", "questions")
    op.drop_index("idx_questions_bloom_level", "questions")
    op.drop_index("idx_questions_difficulty", "questions")
    op.drop_index("idx_questions_document_id", "questions")
    op.drop_index("idx_chunks_document_chunk", "chunks")
    op.drop_index("idx_chunks_document_id", "chunks")
    op.drop_index("idx_documents_created_at", "documents")
    op.drop_index("idx_documents_content_type", "documents")
    op.drop_index("idx_documents_status", "documents")

    # Drop tables
    op.drop_table("questions")
    op.drop_table("chunks")
    op.drop_table("documents")
