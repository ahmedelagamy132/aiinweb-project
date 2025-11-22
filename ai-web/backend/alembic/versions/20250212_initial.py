"""Initial migration creating persistence for echo, plans, resources, and RAG chunks.

Revision ID: 20250212_initial
Revises: 
Create Date: 2025-02-12
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20250212_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "echo_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_key", sa.String(length=255), nullable=False),
        sa.Column("failures", sa.Integer(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_echo_attempts_client_key"), "echo_attempts", ["client_key"], unique=False)

    op.create_table(
        "plan_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("goal", sa.String(length=255), nullable=False),
        sa.Column("audience_role", sa.String(length=120), nullable=False),
        sa.Column("audience_experience", sa.String(length=32), nullable=False),
        sa.Column("primary_risk", sa.String(length=255), nullable=True),
        sa.Column("include_risks", sa.Boolean(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("plan", sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "resources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("difficulty", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_document_chunks_slug"), "document_chunks", ["slug"], unique=False)

    seed_data = [
        {
            "slug": "stack-overview",
            "source": "docs/stack",
            "content": "Docker Compose runs Postgres, FastAPI, Vite, and Nginx. Migrations are applied via Alembic before the app starts.",
        },
        {
            "slug": "rag-notes",
            "source": "docs/rag",
            "content": "The chatbot retrieves markdown snippets from the repository, ranks them with a hashed embedding, and feeds the context into Gemini when configured.",
        },
        {
            "slug": "frontend",
            "source": "docs/frontend",
            "content": "The React app consumes real API endpoints for echo retries, planner history, resources, and the chatbot UI.",
        },
    ]

    conn = op.get_bind()

    for entry in seed_data:
        conn.execute(
            sa.text(
                "INSERT INTO document_chunks (slug, source, content, embedding, created_at) "
                "VALUES (:slug, :source, :content, '[]', now())"
            ).bindparams(**entry)
        )

    resource_seed = [
        {
            "title": "Alembic migrations guide",
            "description": "Step-by-step instructions for creating and applying schema migrations in this template.",
            "url": "https://alembic.sqlalchemy.org/en/latest/tutorial.html",
            "difficulty": "intermediate",
        },
        {
            "title": "FastAPI SQLAlchemy patterns",
            "description": "Reference patterns for dependency-injected sessions and CRUD helpers.",
            "url": "https://fastapi.tiangolo.com/tutorial/sql-databases/",
            "difficulty": "beginner",
        },
        {
            "title": "Gemini quickstart",
            "description": "Configure the GEMINI_API_KEY and experiment with the RAG chatbot prompts.",
            "url": "https://ai.google.dev/gemini-api/docs/quickstart",
            "difficulty": "advanced",
        },
    ]
    for entry in resource_seed:
        conn.execute(
            sa.text(
                "INSERT INTO resources (title, description, url, difficulty, created_at, updated_at) "
                "VALUES (:title, :description, :url, :difficulty, now(), now())"
            ).bindparams(**entry)
        )


def downgrade() -> None:
    op.drop_index(op.f("ix_document_chunks_slug"), table_name="document_chunks")
    op.drop_table("document_chunks")
    op.drop_table("resources")
    op.drop_table("plan_runs")
    op.drop_index(op.f("ix_echo_attempts_client_key"), table_name="echo_attempts")
    op.drop_table("echo_attempts")

